def create_grass_detection_summary(
    grass_confidence: float, weed_confidence: float
) -> str:
    summary = "Use model prediction information with care when making decisions."

    if grass_confidence < 0.01 and weed_confidence < 0.01:
        summary = "Unable to detect either Grass or Weed with confidence."
    elif grass_confidence > 0.8 and weed_confidence < 0.1:
        summary = (
            "The area analyzed is most likely all Grass and maybe little or no Weed."
        )
    elif grass_confidence > 0.6 and weed_confidence < 0.1:
        summary = "The area analyzed has good chance of Grass but not enough confidence to determine the presence of Weed."
    elif grass_confidence > 0.40 and weed_confidence < 0.1:
        summary = "There is a good chance of Grass but not enough confidence for Weed."
    elif grass_confidence > 0.3 and weed_confidence < 0.1:
        summary = "Possibly some grass but not enough confidence to determine the presence of Weed"
    elif grass_confidence <= 0.3 and weed_confidence <= 0.3:
        summary = "Very low chances of either Grass and Weed."
    elif grass_confidence > 0.8 and weed_confidence > 0.8:
        summary = "Very high chance your lawn has both Grass and Weed."
    elif grass_confidence > 0.3 and weed_confidence > 0.3:
        summary = "There is a moderate chance that your lawn has both Grass and Weed."

    # from weed perspective
    elif weed_confidence > 0.8 and grass_confidence < 0.1:
        summary = (
            "The area analyzed is most likely all Weed with very low chance of Grass."
        )
    elif weed_confidence > 60.0 and grass_confidence < 0.1:
        summary = (
            "The area analyzed most likely has Weed with very low chance of Grass."
        )
    elif weed_confidence > 0.40 and grass_confidence < 0.1:
        summary = "There is a good chance of Weed but not enough confidence for Grass."
    elif weed_confidence > 0.3 and grass_confidence < 0.1:
        summary = "Possibly good chance of Weed but low likelihood for Grass."
    else:
        summary = (
            "Always use model prediction information with care when making decisions."
        )
    return summary
