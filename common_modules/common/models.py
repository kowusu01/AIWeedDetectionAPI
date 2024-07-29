class GrassPredictionData:
    def __init__(self, name: str, confidence_level: int, bounding_box: any) -> None:
        self.name = name
        self.confidence_level = confidence_level
        self.bounding_box = bounding_box


class MarkedDetectedArea:
    def __init__(
        self, name: str, confidence_level: int, marked_color: str, bounding_box: any
    ) -> None:
        self.name = name
        self.confidence_level = confidence_level
        self.marked_color = marked_color
        self.bounding_box = bounding_box

    def to_dict(self):
        return {
            "predictedLabel": self.name,
            "confidenceLevel": self.confidence_level,
            "color": self.marked_color,
        }


class GrassAnalysisResponse:

    def __init__(
        self,
        predictions_image_url: str,
        predictions_info_url: str,
        timestamp: str,
        top_n: int,
        summary: str,
        detected_details: list[GrassPredictionData],
    ) -> None:
        self.predictions_image_url = predictions_image_url
        self.predictions_info_url = predictions_info_url
        self.timestamp = timestamp
        self.top_n = top_n
        self.summary = summary
        self.detected_details = detected_details

    def to_dict(self):
        return {
            "prediction_image_url": self.predictions_image_url,
            "prediction_info_url": self.predictions_info_url,
            "timestamp": self.timestamp,
            "top_n": self.top_n,
            "summary": self.summary,
            "detected_details": [d.to_dict() for d in self.detected_details],
        }
