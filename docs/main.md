# Introduction
This project proposes a possible next step for the free-text data processing capabilities implemented as [CogStack-Pipeline](https://github.com/CogStack/CogStack-Pipeline), shaping the solution more towards Platform-as-a-Service.
CogStack-NiFi contains example recipes using [Apache NiFi](https://nifi.apache.org/) as the key data workflow engine with a set of services for documents processing with NLP.
Each component implementing key functionality, such as Text Extraction or Natural Language Processing, runs as a service where the data routing between the components and data source/sink is handled by Apache NiFi.
Moreover, NLP services are expected to implement an uniform RESTful API to enable easy plugging-in into existing document processing pipelines, making it possible to use any NLP application in the stack.


## Project organisation
The project is organised in the following directories:
- [`./nifi`](nifi.md) - custom Docker image of Apache NiFi with configuration files, drivers, example workflows and custom user resources,
- [`./security`](security.md) - scripts to generate SSL keys and certificates for Apache NiFi and related services (when needed) with other security-related requirements,
- [`./services`](services.md) - available services with their corresponding configuration files and resources,
- [`./deploy`](deploy/main.md) - an example deployment of Apache NiFi with related services.
- [`./scripts`](https://github.com/CogStack/CogStack-NiFi/tree/master/scripts) - helper scripts such as the one ingesting samples into Elasticsearch.

For more information please refer follow this guide that walks through example use cases, workflows and technical setup and configuration.

As a good starting point, please see [here](deploy/main.md) for more details on running an example project deployment.

## IMPORTANT NEWS AND UPDATES

Please check [IMPORTANT NEWS](./news.md) for any major changes that might affect your deployment and <strong>security problems</strong> that have been discovered.