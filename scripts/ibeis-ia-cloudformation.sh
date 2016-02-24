#!/bin/bash -ex
# Get WAITHANDLE, kinda awkward as it needs to be defined before error_exit
export WAITHANDLE=$1
# Helper function.
function error_exit
{
  cfn-signal -e 1 -r $1 $WAITHANDLE
  exit 1
}
# Check parameters
if [ $# -ne 3 ]; then
    echo "usage: $0 { 'Ref': 'WaitHandle' } { 'Ref': 'AWS::StackId' } { 'Ref': 'AWS::Region' }"
    error_exit 'Invalid parameters.'
fi
# Get Parameters, including WAITHANDLE redefine
export WAITHANDLE=$1 # { 'Ref': 'WaitHandle' }
export STACKID=$2 # { 'Ref': 'AWS::StackId' }
export REGION=$3 # { 'Ref': 'AWS::Region' }
# Update apt-get.
sudo aptdcon --refresh || error_exit 'Failed apt-get update.'
yes | sudo aptdcon --install ruby2.0 || error_exit 'Failed apt-get install ruby2.0.'
yes | sudo aptdcon --install python-pip || error_exit 'Failed apt-get install python-pip'
yes | sudo aptdcon --install python-setuptools || error_exit 'Failed apt-get install python-setuptools.'
pip install -U awscli || error_exit 'Failed pip install awscli.'
# Install the AWS CloudFormation Agent.
mkdir aws-cfn-bootstrap-latest
curl https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz | tar xz -C aws-cfn-bootstrap-latest --strip-components 1 || error_exit 'Failed to download AWS CloudFormation Agent.'
easy_install aws-cfn-bootstrap-latest || error_exit 'Failed to install AWS CloudFormation Agent.'
# Install the AWS CodeDeploy Agent.
mkdir aws-cd-install-latest
cd aws-cd-install-latest
aws s3 cp --region $REGION s3://aws-codedeploy-$REGION/latest/install . || error_exit 'Failed to download AWS CodeDeploy Agent.'
sudo chmod +x ./install
sudo ./install auto || error_exit 'Failed to install AWS CodeDeploy Agent.'
# Start the stack initialization
cfn-init -s $STACKID -r LinuxEC2Instance --region $REGION || error_exit 'Failed to run cfn-init.'
# All is well, so signal success to the stack.
cfn-signal -e 0 -r 'AWS CloudFormation and CodeDeploy Agents setup complete.' $WAITHANDLE
cd ..
sudo rm -rf init.config init.log
sudo rm -rf aws-cd-install-latest
sudo rm -rf aws-cfn-bootstrap-latest
sudo rm -rf ibeis-ia-cloudformation.sh
