import PIL.Image
import google.generativeai as genai
genai.configure(api_key="AIzaSyAxhU6n6FWwQbcR6bvPcLBQX_S5YdpLYHY")
#genai.configure(api_key="AIzaSyABWxUrpQ1ycQmUIlJc6gJZTiSg5xvg6Tg")


def classify_image(image_path):
    img = PIL.Image.open(image_path)
    model = genai.GenerativeModel('gemini-1.5-pro')
    #temporary to decrease token usage
    prompt = ("Classify the plant")
    '''
    prompt = (
        "You are a plant expert. Based on the image of the plant I provide, "
        "please identify the plant species or the closest match. "
        "Then give the recommended growing conditions, including:\n"
        "- Soil moisture (e.g., low/medium/high)\n"
        "- Light exposure (e.g., full sun, partial shade, indirect light)\n"
        "- Humidity levels\n"
        "- Ideal temperature range (°C or °F)\n"
        "Be concise but complete. If the plant can't be clearly identified, say so."
    )
    '''
    response = model.generate_content([prompt, img])
    print(response.text)
    return response.text

