# Update the weights in an ALB Load Balancing Cloudlet

This tool modifies the weights (%) in a Load Balancing ID used by the Application Load Balancer Cloudlet.

The user can optionally select to immediately push the change to staging or production by using the '-x' option. Also the user can optionally chose to work based on the active version in staging or production by using the '-s' option.


## USAGE:

The script has three main commands, each with with sub functions.

```
usage: cloudlet_alb_balancing.py [--version]  ...

Application Load Balancer Cloudlet Weitghts Updater

optional arguments:
  --version  show program's version number and exit

Commands:

    help     Show available help
    update   Modify target rule
    activate
             Activate a Load Balancing ID to Staging or Production
    search   Search for policies and load balancing IDs
```

* [Update Weights](#update)
* [Activate Load Balancing ID](#activate)
* [Search](#search)

### Update
Update the weights on a Load Balancing ID. A new balancing ID is created from the existing version activated on Staging or Production.


```
usage: cloudlet_alb_balancing.py update --loadid LOADID --datacenters
                                        DATACENTERS [--stage]
                                        [--activate {STAGING,PRODUCTION}]
                                        [--edgerc EDGERC] [--section SECTION]
                                        [--verbose]

required arguments:
  --loadid LOADID       Load Balancing ID name
  --datacenters DATACENTERS
                        Data Center Name and Percentge Value, Example:
                        'DC1:20,DC2:35,DC3:45'

optional arguments:
  --stage               Work based on the last active verion in staging. By
                        default the script works on the last version activated
                        in production
  --activate {STAGING,PRODUCTION}
                        Activate the policy to the specified network. Default
                        is PRODUCTION
  --edgerc EDGERC       Config file [default: ~/.edgerc]
  --section SECTION     Config section in .edgerc [default: cloudlets]
  --verbose             Enable verbose mode
```

### Activate
Activate an existing Load Balancing ID. No modifications are made to the weights.

```
usage: cloudlet_alb_balancing.py activate --loadid LOADID --version VERSION
                                          [--network {STAGING,PRODUCTION}]
                                          [--edgerc EDGERC]
                                          [--section SECTION] [--verbose]

required arguments:
  --loadid LOADID       Load Balancing ID name
  --version VERSION     Version of the Load Balancing ID to activate

optional arguments:
  --network {STAGING,PRODUCTION}
                        Activate the policy to the specified network. Default
                        is PRODUCTION
  --edgerc EDGERC       Config file [default: ~/.edgerc]
  --section SECTION     Config section in .edgerc [default: cloudlets]
  --verbose             Enable verbose mode
```

### Search
* Search the associated load balancing IDs and properties to an ALB policy.
* Search the associated ALB policy name and properties to a load balancing Id.

The results are displayed in a trew view form.

```
usage: cloudlet_alb_balancing.py search --type {loadid,policy} --name NAME
                                        [--edgerc EDGERC] [--section SECTION]

required arguments:
  --type {loadid,policy}
                        Select to search for a policy or load balancing ID
  --name NAME           Name to search for

optional arguments:
  --edgerc EDGERC       Config file [default: ~/.edgerc]
  --section SECTION     Config section in .edgerc [default: cloudlets]
```