import traceback
import io
import json
import os
import sys

# jython packages
from org.apache.commons.io import IOUtils
from org.apache.nifi.processor.io import StreamCallback, OutputStreamCallback
import org.apache.nifi.logging.ComponentLog
from org.python.core.util import StringUtil

global flowFile

global DOCUMENT_ID_FIELD_NAME

global ANNOTATION_ID_FIELD_NAME
global ANNOTATION_TYPES_TO_IGNORE

flowFile = session.get()

flowFiles = []

FIELD_NLP_PREFIX = 'nlp.'
FIELD_META_PREFIX = 'meta.'

class WriteContentCallback(OutputStreamCallback):
    def __init__(self, content):
        self.content_text = content

    def process(self, outputStream):
        try:
            outputStream.write(StringUtil.toBytes(self.content_text))
        except:
            traceback.print_exc(file=sys.stdout)
            raise

class PyStreamCallback(StreamCallback):
    def __init__(self):
        pass

    def process(self, inputStream, outputStream):
        bytes_arr = IOUtils.toByteArray(inputStream)
        bytes_io = io.BytesIO(bytes_arr)

        json_data_records = json.loads(bytes_io.read())

        result = json_data_records["result"]
        medcat_info = json_data_records["medcat_info"]
        
        for annotated_text_record in result:
            annotations = annotated_text_record["annotations"]
            footer = annotated_text_record["footer"]

            new_footer = {}

            assert DOCUMENT_ID_FIELD_NAME in footer.keys()
            doc_id = footer[DOCUMENT_ID_FIELD_NAME]

            for k,v in footer.iteritems():
                if k in ORIGINAL_FIELDS_TO_INCLUDE:
                    new_footer[FIELD_META_PREFIX + k] = v

            for annotation in annotations:
                new_ann_record = {}
                annotation_data = annotation.values()[0]

                ignore_annotation = False
                for type_to_ignore in ANNOTATION_TYPES_TO_IGNORE:
                    if type_to_ignore in annotation_data["types"]:
                        log.info("====================")
                        ignore_annotation = True
                        break
                
                if ignore_annotation is False:
                    for k,v in annotation_data.iteritems():
                        new_ann_record[FIELD_NLP_PREFIX + str(k)] = v

                        # create the new _id for the annotation record in ElasticSearch
                        
                        new_ann_record["timestamp"] = annotated_text_record["timestamp"]
                        new_ann_record["service_model"] = medcat_info["service_model"]
                        new_ann_record["service_version"] = medcat_info["service_version"]

                        new_ann_record[FIELD_META_PREFIX + DOCUMENT_ID_FIELD_NAME] = doc_id
                        new_ann_record.update(new_footer)
                        
                        document_annotation_id = str(doc_id) + "_" + str(annotation_data[ANNOTATION_ID_FIELD_NAME])

                        new_flow_file = session.create(flowFile)
                        new_flow_file = session.putAttribute(new_flow_file, "document_annotation_id", document_annotation_id)
                        
                        new_flow_file = session.write(new_flow_file, WriteContentCallback(json.dumps(new_ann_record).encode("UTF-8")))
                        flowFiles.append(new_flow_file)


if flowFile != None:
    DOCUMENT_ID_FIELD_NAME = str(context.getProperty("document_id_field"))
    ANNOTATION_ID_FIELD_NAME = str(context.getProperty("annotation_id_field"))

    _tmp_ann_type_ignore = str(context.getProperty("ignore_annotation_types"))

    _tmp_original_record_fields_to_include = str(context.getProperty("original_record_fields_to_include"))
    ORIGINAL_FIELDS_TO_INCLUDE = _tmp_ann_type_ignore.split(",") if _tmp_ann_type_ignore.lower() != "none" else []

    ANNOTATION_TYPES_TO_IGNORE = _tmp_ann_type_ignore.split(",") if _tmp_ann_type_ignore.lower() != "none" else []

    try:
        flowFile = session.write(flowFile, PyStreamCallback())

        session.transfer(flowFiles, REL_SUCCESS)
        session.remove(flowFile)
    except Exception as exception:
        log.error(traceback.format_exc())
        session.transfer(flowFile, REL_FAILURE)

else:
    session.transfer(flowFile, REL_FAILURE)

