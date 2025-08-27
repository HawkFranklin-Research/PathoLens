import os
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
from PIL import Image

from transformers import AutoProcessor, AutoModel

try:
    from ez_wsi_dicomweb import credential_factory
    from ez_wsi_dicomweb import dicom_slide
    from ez_wsi_dicomweb.ml_toolkit import dicom_path
except Exception as e:
    raise RuntimeError("ez-wsi-dicomweb is required for MedSigLIP patch fetching") from e


@dataclass
class Patch:
    x_origin: int
    y_origin: int
    width: int
    height: int


def _to_patch(obj: Dict[str, Any]) -> Patch:
    return Patch(
        x_origin=int(obj["x_origin"]),
        y_origin=int(obj["y_origin"]),
        width=int(obj["width"]),
        height=int(obj["height"]),
    )


class MedSigLIPPredictor:
    """Loads google/medsiglip-448 and returns embeddings for DICOM patches."""

    def __init__(self, model_id: str = "google/medsiglip-448") -> None:
        self.model_id = model_id
        self.model_dir = os.environ.get('MEDSIGLIP_MODEL_DIR')
        self._model = None
        self._processor = None

    def _lazy_load(self):
        if self._model is None or self._processor is None:
            # Try local directory first if provided
            load_from = self.model_dir or self.model_id
            try:
                self._model = AutoModel.from_pretrained(load_from)
                self._processor = AutoProcessor.from_pretrained(load_from)
            except Exception:
                # Fallback to hub
                self._model = AutoModel.from_pretrained(self.model_id)
                self._processor = AutoProcessor.from_pretrained(self.model_id)

    def _credential_factory(self, bearer_token: Optional[str]):
        if bearer_token:
            return credential_factory.TokenPassthroughCredentialFactory(bearer_token)
        return credential_factory.NoAuthCredentialsFactory()

    def _fetch_patch_images(
        self,
        series_path: str,
        patches: List[Patch],
        bearer_token: Optional[str],
        instance_uid: Optional[str] = None,
    ) -> List[Image.Image]:
        cf = self._credential_factory(bearer_token)
        dpath = dicom_path.FromString(series_path)
        ds = dicom_slide.DicomSlide(dwi=None, path=dpath, credential_factory=cf)
        level = None
        if instance_uid:
            # If instance UID provided, use its level; else use base level
            level = ds.get_instance_level(instance_uid)
        imgs = []
        for p in patches:
            arr = ds.get_patch(level, p.x_origin, p.y_origin, p.width, p.height)
            # Convert to PIL RGB
            if isinstance(arr, np.ndarray):
                if arr.ndim == 2:
                    arr = np.stack([arr, arr, arr], axis=-1)
                img = Image.fromarray(arr.astype(np.uint8), mode="RGB")
            else:
                img = Image.fromarray(np.array(arr), mode="RGB")
            imgs.append(img)
        return imgs

    def _embed_images(self, images: List[Image.Image]) -> List[List[float]]:
        self._lazy_load()
        # Processor handles resizing/normalization; batching for efficiency
        inputs = self._processor(images=images, return_tensors="pt")
        with np.errstate(all="ignore"):
            with self._model.no_grad():  # type: ignore[attr-defined]
                outputs = self._model(**inputs)
        embeds = outputs.image_embeds.detach().cpu().numpy()
        return [emb.tolist() for emb in embeds]

    def predict(self, body: Dict[str, Any], bearer_token: Optional[str]) -> Dict[str, Any]:
        # Expect: { "instances": [ { "dicom_path": {"series_path": str}, "patch_coordinates": [..], "instance_uids": [optional] } ] }
        instances = body.get("instances", [])
        results = []
        for inst in instances:
            dicom_path_obj = inst.get("dicom_path") or inst
            series_path = dicom_path_obj.get("series_path")
            if not series_path:
                raise ValueError("Missing series_path in instance")

            instance_uids = inst.get("instance_uids", [])
            instance_uid = instance_uids[0] if instance_uids else None
            patch_objs = inst.get("patch_coordinates") or []
            if not patch_objs:
                raise ValueError("Missing patch_coordinates in instance")
            patches = [_to_patch(p) for p in patch_objs]

            # Fetch images and embed
            imgs = self._fetch_patch_images(series_path, patches, bearer_token, instance_uid)
            vectors = self._embed_images(imgs)

            patch_embeddings = [
                {
                    "patch_coordinate": patch_objs[i],
                    "embedding_vector": vectors[i],
                }
                for i in range(len(patch_objs))
            ]
            results.append({"result": {"patch_embeddings": patch_embeddings}})

        return {"predictions": results}
