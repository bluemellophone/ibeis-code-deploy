#!/bin/bash -ex
# Get WAITHANDLE, kinda awkward as it needs to be defined before error_exit
export WAITHANDLE=$1
# Helper function.
function error_exit
{
    sudo cfn-signal -e 1 -r "$1" $WAITHANDLE
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
# Update apt-get
sudo apt-get update || error_exit 'Failed apt-get update.'
# Install dependencies using apt-get
sudo apt-get -y install ruby2.0 || error_exit 'Failed apt-get install ruby2.0.'
sudo apt-get -y install python-pip || error_exit 'Failed apt-get install python-pip'
sudo apt-get -y install python-setuptools || error_exit 'Failed apt-get install python-setuptools.'
# Install dependencies using aptdcon
# sudo apt-get install -y aptdaemon || error_exit 'Failed apt-get install aptdcon.'
# sudo aptdcon --refresh || error_exit 'Failed aptdcon update.'
# yes | sudo aptdcon --install ruby2.0 || error_exit 'Failed aptdcon install ruby2.0.'
# yes | sudo aptdcon --install python-pip || error_exit 'Failed aptdcon install python-pip'
# yes | sudo aptdcon --install python-setuptools || error_exit 'Failed aptdcon install python-setuptools.'
sudo pip install -U awscli || error_exit 'Failed pip install awscli.'
# Install the AWS CloudFormation Agent.
if [ -d aws-cfn-bootstrap-latest ]; then
    sudo rm -rf aws-cfn-bootstrap-latest
fi
sudo mkdir aws-cfn-bootstrap-latest
sudo curl https://s3.amazonaws.com/cloudformation-examples/aws-cfn-bootstrap-latest.tar.gz | sudo tar xz -C aws-cfn-bootstrap-latest --strip-components 1 || error_exit 'Failed to download AWS CloudFormation Agent.'
sudo easy_install aws-cfn-bootstrap-latest || error_exit 'Failed to install AWS CloudFormation Agent.'
# Install the AWS CodeDeploy Agent.
if [ -d aws-cd-install-latest ]; then
    sudo rm -rf aws-cd-install-latest
fi
sudo mkdir aws-cd-install-latest
cd aws-cd-install-latest
sudo aws s3 cp --region $REGION s3://aws-codedeploy-$REGION/latest/install . || error_exit 'Failed to download AWS CodeDeploy Agent.'
sudo chmod +x ./install
sudo ./install auto || error_exit 'Failed to install AWS CodeDeploy Agent.'
# Start the stack initialization
sudo cfn-init -s $STACKID -r LinuxEC2Instance --region $REGION || error_exit 'Failed to run cfn-init.'
# All is well, so signal success to the stack.
sudo cfn-signal -e 0 -r 'AWS CloudFormation and CodeDeploy Agents setup complete.' $WAITHANDLE
cd ..
# sudo rm -rf init.config init.log
# sudo rm -rf aws-cd-install-latest
# sudo rm -rf aws-cfn-bootstrap-latest
# sudo rm -rf ibeis-ia-cloudformation.sh
