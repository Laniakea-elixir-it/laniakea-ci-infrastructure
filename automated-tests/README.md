# Laniakea CI testing module

The Laniakea CI Infrastructure uses a [Testing module](https://github.com/Laniakea-elixir-it/laniakea-ci-infrastructure/tree/test/testing) to test the PaaS, each application deployment and the deployments functionality.

The most important files in this module are:
* `control-script.py` is the main script used to run tests.
* `Tests.py`, where Python functions for each application test are defined.
* `laniakea_dev.yaml` is used to define tests and each of their variables.
* `laniakea_dev_test_mapper.yaml` is used to define the variables for each application test defined in `Tests.py`

The testing module can automatically check that the deployment of an application through Laniakea is working. Additional tests can also be run on an application after its deployment.  To integrate new additional tests for an application, each of these files should be configured correctly:
1. Add the definition of the Python function for the test in the `Tests.py` module
2. Add the variables needed by the test function previously defined in the `laniakea_dev_test_mapper.yaml`
3. Add the test in the `run_more` list variable under the appropriate deployment description in the `laniakea_dev.yaml` file.

If everything is configured correctly, the additional test will be executed by the `control-script.py`, which will source the `Tests.py`, `laniakea_dev_test_mapper.yaml` and the `laniakea_dev.yaml` files for the test definition.

In the next sections, you will see an example on how to add a new test to check that FTP is working in a Galaxy instance deployed with Laniakea.

## Add the function in `Tests.py`
First, the function that will be used to run the FTP test must be added to the `Tests.py` module. This function will be used by `control-script.py` and must have two parameters, `deployment` and `test_vars` (otherwise it will not work with `control-script.py`). Note that the name of the function will be the same that will be used in `lanaiea_dev.yaml` and `laniakea_dev_test_mapper.yaml` to reference the test (see next paragraphs). For example, we define the `ftp` function for this test:
```python
#______________________________________

def ftp_login(host, user, passwd):
    test = FTP(host=host, user=user, passwd=passwd )
    return test

def ftp_upload(test, file_path):
	with open(file_path,'rb') as f:
		fname = os.path.basename(file_path)
		test.storbinary(f'STOR {fname}', f)

def test_ftp(host, file_path, user, password):
	logger.debug(f"Testing FTP on {host} with upload of {file_path}")
	test = ftp_login(host=host, user=user, passwd=password)
	logger.debug(f"FTP connection with {host} established")
	ftp_upload(test=test, file_path=file_path)
	logger.debug(f"File successfully uploaded with FTP")

# This is the function that will be sourced by control-script.py to run the test
def ftp(deployment, test_vars):
	logger.debug(f'Running ftp test...')
	ftp_file_path = test_vars['file_path']
	ftp_user = test_vars['user']
	ftp_password = test_vars['password']
	host = urlparse(deployment.get_endpoint()).netloc
	test_ftp(host=host, file_path=ftp_file_path, user=ftp_user, password=ftp_password)
```

`control-script.py` will call this function passing as first input parameter the deployment object as defined in the [Deployment class](https://github.com/Laniakea-elixir-it/laniakea-ci-infrastructure/blob/c94074b42a1306b83fa5add708d70e95db09f1ea/testing/Deployments.py#L12)  and as second parameter the test variables, [as read](https://github.com/Laniakea-elixir-it/laniakea-ci-infrastructure/blob/c94074b42a1306b83fa5add708d70e95db09f1ea/testing/control-script.py#L161) from the `laniakea_dev_test_mapper.yaml`. The test variables will be in the form of a dictionary, with each key representing the variable name and the value representing the variable value.
For the `ftp` function, the variables that need to be defined in the `laniakea_dev_test_mapper.yaml` file will be `file_path`, `user` and `password`.


## Define the test variables in `laniakea_dev_test_mapper.yaml`
The test functions variables can be indicated in the `laniakea_dev_test_mapper.yaml` file. For the `ftp` function, the variables needed can be added in the following way:
```yaml
test:
  ftp:
    file_path: testing/ftp_files/input_mate1.fastq
    user: admin@admin.com
    password: galaxy_admin_password
```

Under the `test`, a field with the same name as the test function must be added (i.e. `ftp`).The variables added under the `ftp` field will be loaded by the test Python function as a dictionary.
If no variables are needed by the function you want to add, simply add an empty field under `test`. For example, a test called `endpoint` which doesn't need input variables can be added in this file as:
```yaml
test:
  endpoint:
```


## Add the test in `laniakea_dev.yaml`
Finally, a deployment can be tested with the defined test by specifying it in the `laniakea_dev.yaml` file. For example we will add the `ftp` test for a Galaxy deployment:
```yaml
test:
  galaxy:
    name: "galaxy-minimal"
    enabled: yes
    run_more: ['ftp']
    delete: always # always, no, on_success, on_error # TODO add the possibility to not delete the deployment.
    tosca_template: "https://raw.githubusercontent.com/Laniakea-elixir-it/laniakea-dashboard-config/laniakea-v3.0.0/tosca-templates/galaxy.yaml"
    tosca_template_path: "/tmp/laniakea_dev/galaxy.yml"
    inputs:
      instance_flavor: "large"
      storage_size: "50 GB"
      os_distribution: "centos"
      os_version: "7"
      version: "release_21.09"
      admin_api_key: not_very_secret_api_key
      users: []
      instance_description: "Galaxy Live"
```

The `ftp` test added in the `run_more` list variable will inform the `control-script.py` to source the ftp function from the `Tests.py` module and its input parameters from the `laniakea_dev_test_mapper.yaml` file.


## Add Galaxy workflows test
To check that Galaxy deployments are functioning, it may be useful to run some workflows on them. This can be done through the [galaxy_tools](https://github.com/Laniakea-elixir-it/laniakea-ci-infrastructure/blob/c94074b42a1306b83fa5add708d70e95db09f1ea/testing/Tests.py#L73) function in the `Tests.py` module.
This function can be used for any workflow. To define additional workflow test, you just need to modify the `laniakea_dev.yaml` and `laniakea_dev_test_mapper.yaml` files (no need to add any additional Python code). The test name **must** start with `galaxy_tools` 
The test variables in the `laniakea_dev_test_mapper.yaml` **must** be only these two: `wf_file` and `input_file`:
```yaml
test:
  galaxy_tools_mapping:
    wf_file: testing/bioblend_test/workflows/bowtie2_mapping.ga
    input_file: testing/bioblend_test/inputs/input_files.json
```

`wf_file` indicates the path to the Galaxy workflow file, while `input_file` indicates the path to the JSON file for the input data of the workflows. These files should be added to the [bioblend_test](https://github.com/Laniakea-elixir-it/bioblend_test) github repository. The pipeline used to run these tests will automatically download them from it.

The test can now be added to a Galaxy deployment by specifying it in the `laniakea_dev_test_mapper.yaml` file:
```yaml
test:
  galaxy:
    name: "galaxy-minimal"
    enabled: yes
    run_more: ['galaxy_tools_mapping']
    delete: always # always, no, on_success, on_error # TODO add the possibility to not delete the deployment.
    tosca_template: "https://raw.githubusercontent.com/Laniakea-elixir-it/laniakea-dashboard-config/laniakea-v3.0.0/tosca-templates/galaxy.yaml"
    tosca_template_path: "/tmp/laniakea_dev/galaxy.yml"
    inputs:
      instance_flavor: "large"
      storage_size: "50 GB"
      os_distribution: "centos"
      os_version: "7"
      version: "release_21.09"
      admin_api_key: not_very_secret_api_key
      users: []
      instance_description: "Galaxy Live"
```
