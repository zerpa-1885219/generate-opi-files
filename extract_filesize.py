import os
import json
import mysql.connector
from datetime import datetime

def extract_file_info(file_path):
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
        return "s3://" + data["2"]["files"]["file1"]["file_name"], data["2"]["files"]["file1"]["file_size"]



def modify_db(file_data):
    try:
        db_connection = mysql.connector.connect(
            host="localhost",
            user="digitazon_opigno",
            password="1234",
            database="digitazon_opigno"
        )

        cursor = db_connection.cursor()

        # Iterate through each file_path in the dictionary
        for file_path, file_size in file_data.items():
            # Update the URI in file_managed table
            new_file_path = file_path.replace("s3://", "private://lessons/")
            update_query = "UPDATE file_managed SET uri = %s WHERE uri = %s"
            cursor.execute(update_query, (new_file_path, file_path))

            # Insert a record into s3fs_file table
            timestamp = int(datetime.now().timestamp())
            insert_query = "INSERT INTO s3fs_file (uri, filesize, timestamp, dir, version) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(insert_query, (new_file_path, file_size, timestamp, 0, ""))

        # Commit the changes
        db_connection.commit()
        print("Database updated successfully!")

    except mysql.connector.Error as error:
        print("Error updating database:", error)

    finally:
        # Close the database connection
        if db_connection.is_connected():
            cursor.close()
            db_connection.close()

def main(path):
    output = {}
    for folder in os.listdir(path):
        folder_path = os.path.join(path, folder)
        if not os.path.isdir(folder_path):
            continue
        for file in os.listdir(folder_path):
            if file.startswith("export-activity") and file.endswith(".json"):
                file_name, file_size = extract_file_info(os.path.join(folder_path, file))
                output[file_name] = file_size
    modify_db(output)




if __name__ == "__main__":
    main("output")
