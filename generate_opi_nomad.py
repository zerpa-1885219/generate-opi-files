import os
import json
import zipfile
from shutil import copyfile
import re

list_of_files_template_path = "templates/list_of_files.json"
course_template_path = "templates/export-course_name_id.json"
module_template_path = "templates/export-module_name_id.json"
activity_template_path = "templates/export-activity_name_id.json"

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower()
            for text in re.split('([0-9]+)', s)]

def create_output_folder(folder_name):
    output_folder = os.path.join('output', folder_name)
    os.makedirs(output_folder, exist_ok=True)
    return output_folder


def process_course_template(course_name):
    with open(course_template_path, 'r') as file:
        data = json.load(file)

    # Update values in the template
    data["2"]["label"][0]["value"] = course_name
    data["2"]["field_course_description"][0]["value"] = f"<p>Corso {course_name} course</p>\r\n"

    return data


def process_module_template(module_name, module_id):
    with open(module_template_path, 'r') as file:
        data = json.load(file)

    # Update main key to actual module_id
    data[module_id] = data.pop("2")

    # Update values in the template
    data[module_id]["id"][0]["value"] = module_id
    data[module_id]["vid"][0]["value"] = module_id

    data[module_id]["managed_content"]["id"][0]["value"] = module_id + 7
    data[module_id]["managed_content"]["entity_id"][0]["value"] = module_id
    data[module_id]["managed_content"]["coordinate_y"][0]["value"] = module_id

    data[module_id]["name"][0]["value"] = module_name
    data[module_id]["description"][0]["value"] = f"<p>Modulo {module_name}</p>\r\n"

    if module_id != 1:
        data[module_id]["parent_links"] = [{
            "group_id": "2",
            "parent_content_id": f"{module_id - 1 + 7}",
            "child_content_id": f"{module_id}",
            "required_score": "0",
            "required_activities": []
        }]

    return data


def format_activity_name(activity_name):
    return activity_name.replace('.mp4', '')


def process_activity_template(activity_name, activity_path, activity_size):
    with open(activity_template_path, 'r') as file:
        data = json.load(file)

    # Capitalize first letter
    formatted_activity_name = format_activity_name(activity_name)

    data["2"]["name"][0]["value"] = formatted_activity_name
    data["2"]["files"]["file1"]["file_name"] = activity_path
    data["2"]["files"]["file1"]["file_size"] = activity_size

    print(activity_path)

    return data


def format_file_name(name, type, id):
    return f"export-{type}_{name}_{id}.json"


def save_output(output_folder, file_name, data):
    output_file_path = os.path.join(output_folder, file_name)
    with open(output_file_path, 'w') as output_file:
        json.dump(data, output_file, indent=2)


def create_archive(output_folder, folder_name):
    files_folder = os.path.join(output_folder, folder_name)
    archive_path = os.path.join(output_folder, f"{folder_name}.opi")
    with zipfile.ZipFile(archive_path, 'w') as archive:
        for root, _, files in os.walk(files_folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, files_folder)
                archive.write(file_path, arcname=arcname)

def main(folder_path):
    # Get folder path from the user
    # folder_path = input("Enter the folder path: ").strip()

    # Get folder name (last part of the path)
    course_name = folder_path.split('/')[-1]

    # Create output folder
    output_folder = create_output_folder(course_name)

    # Process and save course template
    course_id = 2
    course_data = process_course_template(course_name)
    course_file_name = format_file_name(course_name, 'course', course_id)
    save_output(output_folder, course_file_name, course_data)

    list_of_files_data = {"course": course_file_name, "modules": {}, "activities": {}}

    modules = []
    activities = []

    current_module_id = 1
    current_activity_id = 1
    # for each file in the folder_path, check if it is a folder, and if so, add it to the list of modules
    for module_name in sorted(os.listdir(folder_path), key=natural_sort_key):
        if os.path.isdir(os.path.join(folder_path, module_name)):

            # Process and save module template
            module_data = process_module_template(module_name, current_module_id)

            module_file_name = format_file_name(module_name, 'module', current_module_id)

            list_of_files_data["modules"][module_name] = module_file_name
            list_of_files_data["activities"][module_name] = []
            save_output(output_folder, module_file_name, module_data)

            # for each file inside of the module folder, check if it is an mp4 file, if so, add it to activities
            for activity_name in sorted(os.listdir(os.path.join(folder_path, module_name)), key=natural_sort_key):
                if activity_name.endswith('.mp4'):
                    # Process and save activity template
                    activity_path = f"{course_name}/{module_name}/{activity_name}"
                    activity_size = os.path.getsize(os.path.join(folder_path, module_name, activity_name))
                    activity_data = process_activity_template(activity_name, activity_path, activity_size)
                    acitivity_file_name = format_file_name(activity_name, 'activity', current_activity_id)
                    list_of_files_data["activities"][module_name].append(acitivity_file_name)

                    save_output(output_folder, acitivity_file_name, activity_data)

                    activities.append(activity_name)
                    current_activity_id += 1

            modules.append(module_name)
            current_module_id += 1

    # Save list of files
    output_list_of_files_path = os.path.join(output_folder, 'list_of_files.json')
    with open(output_list_of_files_path, 'w') as output_file:
        json.dump(list_of_files_data, output_file, indent=2)

    # Create archive
    create_archive('output', course_name)

if __name__ == "__main__":
    print("Starting...")
    path = "/home/juan/Downloads/COURSE TEST/input/Digital nomad/Digital Nomad"
    main(path)