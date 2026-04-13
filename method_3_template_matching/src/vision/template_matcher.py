import cv2

def find_icon(screen_path, template_path, threshold=0.8):
    screen = cv2.imread(screen_path)
    template = cv2.imread(template_path)

    if screen is None:
        raise ValueError("Screen image not found")

    if template is None:
        raise ValueError("Template image not found")

    # Convert to grayscale
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screen_gray, template_gray, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)

    if max_val < threshold:
        return None

    h, w = template_gray.shape
    center_x = max_loc[0] + w // 2
    center_y = max_loc[1] + h // 2
    cv2.rectangle(screen, max_loc, (max_loc[0]+w, max_loc[1]+h), (0,255,0), 2)
    return (center_x, center_y)