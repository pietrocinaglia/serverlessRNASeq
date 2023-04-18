## Serverless computing for mapping RNA-Seq reads to a reference genome.


### Short description
The proposed solution allows mapping sequencing reads to a reference genome. We deployed it on our own architecture based on the serverless computing service (named Lambda) provided by Amazon Web Service (AWS).
The serverless environment was configured as follows:
- Ephemeral storage: 512 MB (maximum is 512 MB);
- Memory: 3,008 MB;
- Virtual CPUs (vCPUs): 2.

Note that more information will be provided on reasonable request.


### Files available into this repository

- lambda_architecture.pdf : it is the architecture that our solution needs for working.

- lambda_function.py : it is a non-exhaustive adaptation of the lambda function for testing purpose only. The paths for a generic sample are already defined in the function, so you don't have to configure a trigger to test this function.

- results.xlsx : it is the results produced during experimentation.

- output_sample1_lambda.txt : an output produced by the proposed solution on a random sample.

- output_sample1_local.txt : an output produced by the a loval workstation the same sample used for output_sample1_lambda.txt .
