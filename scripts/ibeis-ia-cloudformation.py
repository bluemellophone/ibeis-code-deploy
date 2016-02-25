from __future__ import absolute_import, division, print_function
import json


template_structure = '''
{{
    "Description": "Create instances ready for IBEIS IA CodeDeploy.",
    "AWSTemplateFormatVersion": "2010-09-09",
    "Parameters": {{
        "TagKey": {{
            "Description": "The tag key that identifies this as a target for deployments.",
            "Type": "String",
            "Default": "Name",
            "AllowedPattern": "{{pattern}}",
            "ConstraintDescription": "Can contain only ASCII characters."
        }},
        "TagValue": {{
            "Description": "The tag value that identifies this as a target for deployments.",
            "Type": "String",
            "Default": "IBEIS-IA-CodeDeploy",
            "AllowedPattern": "{{pattern}}",
            "ConstraintDescription": "Can contain only ASCII characters."
        }},
        "KeyPairName": {{
            "Description": "Name of an existing Amazon EC2 key pair to enable SSH or RDP access to the instances.",
            "Type": "AWS::EC2::KeyPair::KeyName",
            "Default": "shared-ibeis-team-key"
        }},
        "InstanceType": {{
            "Description": "Amazon EC2 instance type.",
            "Type": "String",
            "Default": "c3.large",
            "ConstraintDescription": "Must be a valid Amazon EC2 instance type.",
            "AllowedValues": [
                "t1.micro",
                "m3.medium",
                "m3.large",
                "m3.xlarge",
                "c3.large",
                "c3.xlarge"
            ]
        }},
        "InstanceCount": {{
            "Description": "Number of Amazon EC2 instances.",
            "Type": "Number",
            "Default": "1",
            "ConstraintDescription": "Must be a number between 1 and {number}.",
            "AllowedValues": [
                {template_number_str}
            ]
        }}
    }},
    "Mappings": {{
        "RegionOS2AMI": {{
            "{region}": {{
                "{os}": "{ami}"
            }}
        }}
    }},
    "Conditions": {{
        {template_condition_str}
    }},
    "Resources": {{
        "WaitHandle": {{
            "Type": "AWS::CloudFormation::WaitConditionHandle"
        }},
        "WaitCondition": {{
            "Type": "AWS::CloudFormation::WaitCondition",
            "Properties": {{
                "Count": {{
                    "Ref": "InstanceCount"
                }},
                "Handle": {{
                    "Ref": "WaitHandle"
                }},
                "Timeout": "900"
            }}
        }},
        "SecurityGroup": {{
            "Type": "AWS::EC2::SecurityGroup",
            "Properties": {{
                "GroupDescription": "Enable HTTP access via ports 80, 5000 and SSH access.",
                "SecurityGroupIngress": [{{
                    "IpProtocol": "tcp",
                    "FromPort": "80",
                    "ToPort": "80",
                    "CidrIp": "0.0.0.0/0"
                }}, {{
                    "IpProtocol": "tcp",
                    "FromPort": "22",
                    "ToPort": "22",
                    "CidrIp": "0.0.0.0/0"
                }}, {{
                    "IpProtocol": "tcp",
                    "FromPort": "5000",
                    "ToPort": "5000",
                    "CidrIp": "0.0.0.0/0"
                }}]
            }}
        }},
        "CodeDeployTrustRole": {{
            "Type": "AWS::IAM::Role",
            "Properties": {{
                "AssumeRolePolicyDocument": {{
                    "Statement": [
                        {{
                            "Sid": "1",
                            "Effect": "Allow",
                            "Principal": {{
                                "Service": [
                                    "codedeploy.us-west-2.amazonaws.com"
                                ]
                            }},
                            "Action": "sts:AssumeRole"
                        }}
                    ]
                }},
                "Path": "/"
            }}
        }},
        "CodeDeployRolePolicies": {{
            "Type": "AWS::IAM::Policy",
            "Properties": {{
                "PolicyName": "CodeDeployPolicy",
                "PolicyDocument": {{
                    "Statement": [{{
                        "Effect": "Allow",
                        "Resource": [
                            "*"
                        ],
                        "Action": [
                            "ec2:Describe*"
                        ]
                    }}, {{
                        "Effect": "Allow",
                        "Resource": [
                            "*"
                        ],
                        "Action": [
                            "autoscaling:CompleteLifecycleAction",
                            "autoscaling:DeleteLifecycleHook",
                            "autoscaling:DescribeLifecycleHooks",
                            "autoscaling:DescribeAutoScalingGroups",
                            "autoscaling:PutLifecycleHook",
                            "autoscaling:RecordLifecycleActionHeartbeat"
                        ]
                    }}, {{
                        "Effect": "Allow",
                        "Resource": [
                            "*"
                        ],
                        "Action": [
                            "Tag:getResources",
                            "Tag:getTags",
                            "Tag:getTagsForResource",
                            "Tag:getTagsForResourceList"
                        ]
                    }}]
                }},
                "Roles": [{{
                    "Ref": "CodeDeployTrustRole"
                }}]
            }}
        }},
        "InstanceRole": {{
            "Type": "AWS::IAM::Role",
            "Properties": {{
                "AssumeRolePolicyDocument": {{
                    "Statement": [{{
                        "Effect": "Allow",
                        "Principal": {{
                            "Service": [
                                "ec2.amazonaws.com"
                            ]
                        }},
                        "Action": [
                            "sts:AssumeRole"
                        ]
                    }}]
                }},
                "Path": "/"
            }}
        }},
        "InstanceRolePolicies": {{
            "Type": "AWS::IAM::Policy",
            "Properties": {{
                "PolicyName": "InstanceRole",
                "PolicyDocument": {{
                    "Statement": [{{
                        "Effect": "Allow",
                        "Action": [
                            "autoscaling:Describe*",
                            "cloudformation:Describe*",
                            "cloudformation:GetTemplate",
                            "s3:Get*",
                            "s3:List*"
                        ],
                        "Resource": "*"
                    }}]
                }},
                "Roles": [{{
                    "Ref": "InstanceRole"
                }}]
            }}
        }},
        "InstanceRoleInstanceProfile": {{
            "Type": "AWS::IAM::InstanceProfile",
            "Properties": {{
                "Path": "/",
                "Roles": [{{
                    "Ref": "InstanceRole"
                }}]
            }}
        }},
        {template_instance_str}
    }},
    "Outputs": {{
        "CodeDeployTrustRoleARN": {{
            "Value": {{
                "Fn::GetAtt": [
                    "CodeDeployTrustRole",
                    "Arn"
                ]
            }}
        }}
    }}
}}
'''

template_instance = '''
"EC2Instance{index}": {{
    "Condition": "LaunchEC2Instance{index}",
    "Type": "AWS::EC2::Instance",
    "Metadata": {{
        "AWS::CloudFormation::Init": {{
            "services": {{
                "sysvint": {{
                    "codedeploy-agent": {{
                        "enabled": "true",
                        "ensureRunning": "true"
                    }}
                }}
            }}
        }}
    }},
    "Properties": {{
        "ImageId": {{
            "Fn::FindInMap": [
                "RegionOS2AMI", {{
                    "Ref": "AWS::Region"
                }},
                "{os}"
            ]
        }},
        "InstanceType": {{
            "Ref": "InstanceType"
        }},
        "SecurityGroups": [{{
            "Ref": "SecurityGroup"
        }}],
        "UserData": {{
            "Fn::Base64": {{
                "Fn::Join": [
                    "", [
                        "#!/bin/bash\\n",
                        "cd /home/ubuntu/\\n",
                        "echo \\"'", {{ "Ref": "WaitHandle" }}, "' '", {{ "Ref": "AWS::StackId" }}, "' '", {{ "Ref": "AWS::Region" }}, "'\\" > init.config\\n",
                        "sudo curl -O https://raw.githubusercontent.com/bluemellophone/ibeis_aws_codedeploy/master/scripts/ibeis-ia-cloudformation.sh\\n",
                        "chmod +x ./ibeis-ia-cloudformation.sh\\n",
                        "sudo ./ibeis-ia-cloudformation.sh '", {{ "Ref": "WaitHandle" }}, "' '", {{ "Ref": "AWS::StackId" }}, "' '", {{ "Ref": "AWS::Region" }}, "' > init.log\\n"
                    ]
                ]
            }}
        }},
        "KeyName": {{
            "Ref": "KeyPairName"
        }},
        "Tags": [{{
            "Key": {{
                "Ref": "TagKey"
            }},
            "Value": {{
                "Ref": "TagValue"
            }}
        }}],
        "IamInstanceProfile": {{
            "Ref": "InstanceRoleInstanceProfile"
        }}
    }}
}}
'''

template_condition = '''
"LaunchEC2Instance{index}": {template_condition_extend}
'''

template_condition_base = '''
{{
    "Fn::Equals": [
        "{number}", {{
            "Ref": "InstanceCount"
        }}
    ]
}}
'''

template_condition_recursive = '''
{{
    "Fn::Or": [{{
        "Fn::Equals": [
            "{number}", {{
                "Ref": "InstanceCount"
            }}
        ]
    }},
    {template_condition_extend}
    ]
}}
'''


if __name__ == '__main__':
    def template_condition_extend_(number, total):
        if number >= total - 1:
            return template_condition_base.format(
                number=number + 1
            )
        else:
            return template_condition_recursive.format(
                number=number + 1,
                template_condition_extend=template_condition_extend_(
                    number + 1,
                    total
                )
            )

    config = {
        'region' : 'us-west-2',
        'ami'    : 'ami-9dbea4fc',
        'os'     : 'Linux',
        'number' : 20,
    }

    # Compile numbers
    template_number_str = ','.join(
        [
            '"%d"' % (index + 1, )
            for index in range(config.get('number'))
        ]
    )

    # Compile instances
    template_instance_str = ','.join(
        [
            template_instance.format(
                index=index + 1,
                **config
            )
            for index in range(config.get('number'))
        ]
    )

    # Compile conditions
    template_condition_str = ','.join(
        [
            template_condition.format(
                index=index + 1,
                template_condition_extend=template_condition_extend_(
                    index,
                    config.get('number')
                )
            )
            for index in range(config.get('number'))
        ]
    )

    # Compile full template
    template_str = template_structure.format(
        template_number_str=template_number_str,
        template_condition_str=template_condition_str,
        template_instance_str=template_instance_str,
        **config
    )

    # Save to file
    with open('ibeis-ia-cloudformation.new.json', 'w') as output_file:
        parsed = json.loads(template_str)
        json_str = json.dumps(
            parsed,
            sort_keys=True,
            indent=2,
            separators=(',', ': ')
        )
        json_str = json_str.replace('{pattern}', '[\\\\x20-\\\\x7E]*')
        output_file.write(json_str)
