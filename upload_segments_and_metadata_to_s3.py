from tracardi.service.plugin.runner import ActionRunner
from tracardi.service.plugin.domain.result import Result
from tracardi.service.plugin.domain.register import Plugin, Spec, MetaData
from tracardi.service.plugin.domain.register import Form, FormGroup, FormField, FormComponent
from .config import Config
from datetime import datetime
import json
import boto3
import tempfile
import os


def validate(config: dict) -> Config:
    return Config(**config)


class S3SegmentsMetadataUploaderPlugin(ActionRunner):
    config: Config

    async def set_up(self, config):
        self.config = validate(config)

    async def run(self, payload: dict, in_edge=None):
        s3 = boto3.client(
            's3',
            aws_access_key_id=self.config.aws_access_key_id,
            aws_secret_access_key=self.config.aws_secret_access_key
        )
        temp_segments_filename = None
        temp_metadata_filename = None
        try:
            segments_filename = self._generate_filename("segments")
            metadata_filename = self._generate_filename("metadata")
            segments_exists = self._check_s3_keys_exist(s3, self.config.s3_bucket, segments_filename)
            metadata_exists = self._check_s3_keys_exist(s3, self.config.s3_bucket, metadata_filename)

            segments_data = {"profiles": [{"smi_uid": payload['traits']['smi_uid'], "segments": payload['segments']}]}
            if segments_exists:
                temp_segments_filename = self._download_s3_file(s3, self.config.s3_bucket, segments_filename)
                with open(temp_segments_filename, 'r') as segments_file:
                    existing_segments_data = json.load(segments_file)
                    existing_segments_data['profiles'].append(
                        {"smi_uid": payload['traits']['smi_uid'], "segments": payload['segments']}
                    )
                segments_data = existing_segments_data
            self._upload_file_to_s3(s3, self.config.s3_bucket, segments_filename, segments_data)

            metadata_data = {"profiles": [{"segments": payload['segments']}]}
            if metadata_exists:
                temp_metadata_filename = self._download_s3_file(s3, self.config.s3_bucket, metadata_filename)
                with open(temp_metadata_filename, 'r') as metadata_file:
                    existing_metadata_data = json.load(metadata_file)
                    existing_metadata_data['profiles'].append({"segments": payload['segments']})
                metadata_data = existing_metadata_data

            self._upload_file_to_s3(s3, self.config.s3_bucket, metadata_filename, metadata_data)

            return Result(port="UploadSuccess",
                          value={"message": "JSON data uploaded to S3."})

        except Exception as err:
            return Result(port="UploadError", value={"error": f"S3 upload error: {err}"})

        finally:
            if os.path.exists(temp_segments_filename) and os.path.exists(temp_metadata_filename):
                os.remove(temp_segments_filename)
                os.remove(temp_metadata_filename)

    @staticmethod
    def _check_s3_keys_exist(s3_client, bucket: str, keys_to_check: list | str) -> bool:
        response = s3_client.list_objects_v2(Bucket=bucket)
        if 'Contents' in response:
            existing_keys = {item['Key'] for item in response['Contents']}
            return keys_to_check in existing_keys
        return False

    @staticmethod
    def _upload_file_to_s3(s3_client, bucket: str, filename: str, json_data: dict) -> None:
        s3_client.put_object(
            Bucket=bucket,
            Key=filename,
            Body=json.dumps(json_data)
        )

    @staticmethod
    def _download_s3_file(s3_client, bucket: str, filename: str) -> str:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_filename = temp_file.name
            s3_client.download_file(bucket, filename, temp_filename)
            return temp_filename

    @staticmethod
    def _generate_filename(prefix: str) -> str:
        return f"{datetime.now().strftime('%Y-%m-%d')}_{prefix}.json"


def register() -> Plugin:
    return Plugin(
        start=False,
        spec=Spec(
            module=__name__,
            className=S3SegmentsMetadataUploaderPlugin.__name__,
            init={
                "aws_access_key_id": "",
                "aws_secret_access_key": "",
                "s3_bucket": ""
            },
            form=Form(groups=[
                FormGroup(
                    name="S3 Upload Configuration",
                    description="Configure AWS credentials and S3 details",
                    fields=[
                        FormField(
                            id="aws_access_key_id",
                            name="AWS Access Key ID",
                            description="AWS Access Key ID",
                            component=FormComponent(type="password", props={"label": "AWS Access Key ID"})
                        ),
                        FormField(
                            id="aws_secret_access_key",
                            name="AWS Secret Access Key",
                            description="AWS Secret Access Key",
                            component=FormComponent(type="password", props={"label": "AWS Secret Access Key"})
                        ),
                        FormField(
                            id="s3_bucket",
                            name="S3 Bucket",
                            description="S3 Bucket to upload JSON data",
                            component=FormComponent(type="text", props={"label": "S3 Bucket"})
                        ),
                    ]
                ),
            ]),
            inputs=["payload"],
            outputs=["UploadSuccess", "UploadError"],
            license="MIT",
            author="Eqwile"
        ),
        metadata=MetaData(
            name="S3 Uploader Plugin",
            desc='Uploads user profile data to S3 as JSON.',
            group=["AWS"],
            purpose=['collection', 'segmentation']
        )
    )