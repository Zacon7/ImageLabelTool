import os
import json
from PIL import Image

low = 1
img_root = "datasets/舌像处理/"
json_name = "results.json"
region_path = os.path.join(img_root, "region_images")
region_num = 0
region_dict = {}

for low in range(1, 1402, 200):
    data_path = img_root + str(low) + "-" + str(low + 199)
    print(data_path)
    # Load the JSON data
    with open(os.path.join(data_path, json_name), "r", encoding="utf-8") as json_file:
        json_dict = json.load(json_file)

    os.makedirs(region_path, exist_ok=True)

    for image_name, rect_list in json_dict.items():
        image = Image.open(os.path.join(data_path, image_name))
        for rect in rect_list:
            labels = rect["labels"]
            points = rect["points"]

            start_x, start_y = points[0]
            end_x, end_y = points[1]

            start_x, end_x = min(start_x, end_x), max(start_x, end_x)
            start_y, end_y = min(start_y, end_y), max(start_y, end_y)

            if start_x < end_x and start_y < end_y:
                region_img = image.crop((start_x, start_y, end_x, end_y))

                # Save the cropped region as a new image
                region_name = "region_" + str(region_num + 1)
                region_num += 1

                # output_image_name = f'{region_path}/{region_name}.jpg'
                region_img.save(f"{region_path}/{region_name}.jpg")

                if region_name not in region_dict:
                    region_dict[region_name] = []

                region_dict[region_name] = labels

# Save the new JSON data
with open(
    os.path.join(region_path, "region.json"), "w", encoding="utf-8"
) as region_file:
    json.dump(region_dict, region_file, ensure_ascii=False, indent=4)

print("Image cropping and JSON creation completed.")
