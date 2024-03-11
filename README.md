# S3 Segments Uploader Plugin

This plugin is designed to collect and send profile segments to AWS storage.
The plugin accepts a profile as payload. Then receives profile segments and sends to s3 bucket .json file (<current_date>_segments.json). 
The data schema in the file is represented like this

```{"profiles": [{"smi_uid": payload['traits']['smi_uid'], "segments": payload['segments']}]}]} ```

So it is important that there is a ```"smi_uid"``` field in ```traits```

# Dependency installation

You need to install the boto3 package for this plug-in to work. You can install it with pip: ```pip install boto3```. 
Or just add boto3 to ```requirements.txt```

# Configuration
This plugin requires the following configuration parameters:

+ **AWS Access Key ID:** Your AWS Access Key ID.
+ **AWS Secret Access Key:** Your AWS Secret Access Key.
+ **S3 Bucket:** The name of the S3 bucket where you want to upload the JSON data.

# Inputs
**payload:** The data payload to be uploaded to S3. Again, it has to be a profile.

# Outputs
+ **UploadSuccess:** Indicates that the JSON data was successfully uploaded to S3.
+ **UploadError:** Indicates that an error occurred during the upload process.

# Contributing
If you find any issues or have suggestions for improvement, please feel free to open an issue or submit a pull request on GitHub.
