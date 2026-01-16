"""
GSC Coin Cloud Deployment Script
Automated deployment to AWS, GCP, or Azure
"""

import os
import json
import subprocess
import time
import argparse
from typing import Dict, List, Optional

class CloudDeployer:
    """Cloud deployment manager for GSC blockchain"""
    
    def __init__(self, provider: str, region: str = None):
        self.provider = provider.lower()
        self.region = region
        self.project_name = "gsc-mainnet"
        self.image_name = "gsccoin/mainnet-node:latest"
        
        # Default regions
        self.default_regions = {
            'aws': 'us-east-1',
            'gcp': 'us-central1',
            'azure': 'eastus'
        }
        
        if not self.region:
            self.region = self.default_regions.get(self.provider, 'us-east-1')
    
    def deploy_aws(self, instance_count: int = 3) -> Dict:
        """Deploy to AWS using ECS Fargate"""
        print("🚀 Deploying GSC Mainnet to AWS...")
        
        # Create ECS cluster
        cluster_config = {
            "clusterName": f"{self.project_name}-cluster",
            "capacityProviders": ["FARGATE"],
            "defaultCapacityProviderStrategy": [
                {
                    "capacityProvider": "FARGATE",
                    "weight": 1
                }
            ]
        }
        
        # Task definition for GSC node
        task_definition = {
            "family": f"{self.project_name}-task",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "1024",
            "memory": "2048",
            "executionRoleArn": f"arn:aws:iam::ACCOUNT:role/{self.project_name}-execution-role",
            "taskRoleArn": f"arn:aws:iam::ACCOUNT:role/{self.project_name}-task-role",
            "containerDefinitions": [
                {
                    "name": "gsc-node",
                    "image": self.image_name,
                    "portMappings": [
                        {"containerPort": 8333, "protocol": "tcp"},
                        {"containerPort": 8334, "protocol": "tcp"},
                        {"containerPort": 8335, "protocol": "tcp"}
                    ],
                    "environment": [
                        {"name": "GSC_NETWORK", "value": "mainnet"},
                        {"name": "GSC_NODE_TYPE", "value": "regular"}
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{self.project_name}",
                            "awslogs-region": self.region,
                            "awslogs-stream-prefix": "ecs"
                        }
                    },
                    "healthCheck": {
                        "command": [
                            "CMD-SHELL",
                            "curl -f http://localhost:8335/api/v1/info || exit 1"
                        ],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3
                    }
                }
            ]
        }
        
        # Service configuration
        service_config = {
            "serviceName": f"{self.project_name}-service",
            "cluster": f"{self.project_name}-cluster",
            "taskDefinition": f"{self.project_name}-task",
            "desiredCount": instance_count,
            "launchType": "FARGATE",
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": ["subnet-12345", "subnet-67890"],
                    "securityGroups": [f"{self.project_name}-sg"],
                    "assignPublicIp": "ENABLED"
                }
            },
            "loadBalancers": [
                {
                    "targetGroupArn": f"arn:aws:elasticloadbalancing:{self.region}:ACCOUNT:targetgroup/{self.project_name}-tg",
                    "containerName": "gsc-node",
                    "containerPort": 8335
                }
            ]
        }
        
        # Generate CloudFormation template
        cloudformation_template = {
            "AWSTemplateFormatVersion": "2010-09-09",
            "Description": "GSC Coin Mainnet Infrastructure",
            "Resources": {
                "VPC": {
                    "Type": "AWS::EC2::VPC",
                    "Properties": {
                        "CidrBlock": "10.0.0.0/16",
                        "EnableDnsHostnames": True,
                        "EnableDnsSupport": True
                    }
                },
                "InternetGateway": {
                    "Type": "AWS::EC2::InternetGateway"
                },
                "LoadBalancer": {
                    "Type": "AWS::ElasticLoadBalancingV2::LoadBalancer",
                    "Properties": {
                        "Name": f"{self.project_name}-alb",
                        "Scheme": "internet-facing",
                        "Type": "application",
                        "Subnets": [{"Ref": "PublicSubnet1"}, {"Ref": "PublicSubnet2"}]
                    }
                }
            }
        }
        
        # Save configurations
        os.makedirs('aws_deploy', exist_ok=True)
        
        with open('aws_deploy/task_definition.json', 'w') as f:
            json.dump(task_definition, f, indent=2)
        
        with open('aws_deploy/service_config.json', 'w') as f:
            json.dump(service_config, f, indent=2)
        
        with open('aws_deploy/cloudformation.json', 'w') as f:
            json.dump(cloudformation_template, f, indent=2)
        
        print("✅ AWS deployment configurations generated")
        print("📝 Next steps:")
        print("1. Configure AWS CLI: aws configure")
        print("2. Create ECR repository: aws ecr create-repository --repository-name gsccoin/mainnet-node")
        print("3. Push Docker image to ECR")
        print("4. Deploy CloudFormation stack: aws cloudformation create-stack --stack-name gsc-mainnet --template-body file://aws_deploy/cloudformation.json")
        print("5. Create ECS cluster and service using generated configs")
        
        return {
            'provider': 'aws',
            'region': self.region,
            'configs_generated': True,
            'next_steps': 'Manual deployment required'
        }
    
    def deploy_gcp(self, instance_count: int = 3) -> Dict:
        """Deploy to Google Cloud Platform using GKE"""
        print("🚀 Deploying GSC Mainnet to GCP...")
        
        # Kubernetes deployment configuration
        k8s_deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": f"{self.project_name}-deployment",
                "labels": {"app": self.project_name}
            },
            "spec": {
                "replicas": instance_count,
                "selector": {"matchLabels": {"app": self.project_name}},
                "template": {
                    "metadata": {"labels": {"app": self.project_name}},
                    "spec": {
                        "containers": [
                            {
                                "name": "gsc-node",
                                "image": f"gcr.io/PROJECT_ID/{self.image_name}",
                                "ports": [
                                    {"containerPort": 8333, "name": "p2p"},
                                    {"containerPort": 8334, "name": "rpc"},
                                    {"containerPort": 8335, "name": "api"}
                                ],
                                "env": [
                                    {"name": "GSC_NETWORK", "value": "mainnet"},
                                    {"name": "GSC_NODE_TYPE", "value": "regular"}
                                ],
                                "resources": {
                                    "requests": {"cpu": "500m", "memory": "1Gi"},
                                    "limits": {"cpu": "1000m", "memory": "2Gi"}
                                },
                                "livenessProbe": {
                                    "httpGet": {"path": "/api/v1/info", "port": 8335},
                                    "initialDelaySeconds": 60,
                                    "periodSeconds": 30
                                },
                                "readinessProbe": {
                                    "httpGet": {"path": "/api/v1/info", "port": 8335},
                                    "initialDelaySeconds": 30,
                                    "periodSeconds": 10
                                }
                            }
                        ]
                    }
                }
            }
        }
        
        # Service configuration
        k8s_service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {"name": f"{self.project_name}-service"},
            "spec": {
                "selector": {"app": self.project_name},
                "ports": [
                    {"name": "p2p", "port": 8333, "targetPort": 8333},
                    {"name": "rpc", "port": 8334, "targetPort": 8334},
                    {"name": "api", "port": 8335, "targetPort": 8335}
                ],
                "type": "LoadBalancer"
            }
        }
        
        # Ingress configuration
        k8s_ingress = {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {
                "name": f"{self.project_name}-ingress",
                "annotations": {
                    "kubernetes.io/ingress.global-static-ip-name": f"{self.project_name}-ip",
                    "networking.gke.io/managed-certificates": f"{self.project_name}-ssl"
                }
            },
            "spec": {
                "rules": [
                    {
                        "host": "gsccoin.network",
                        "http": {
                            "paths": [
                                {
                                    "path": "/api/*",
                                    "pathType": "ImplementationSpecific",
                                    "backend": {
                                        "service": {
                                            "name": f"{self.project_name}-service",
                                            "port": {"number": 8335}
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }
        
        # Save configurations
        os.makedirs('gcp_deploy', exist_ok=True)
        
        with open('gcp_deploy/deployment.yaml', 'w') as f:
            import yaml
            yaml.dump(k8s_deployment, f, default_flow_style=False)
        
        with open('gcp_deploy/service.yaml', 'w') as f:
            import yaml
            yaml.dump(k8s_service, f, default_flow_style=False)
        
        with open('gcp_deploy/ingress.yaml', 'w') as f:
            import yaml
            yaml.dump(k8s_ingress, f, default_flow_style=False)
        
        # Generate deployment script
        deploy_script = """#!/bin/bash
# GCP Deployment Script for GSC Mainnet

set -e

PROJECT_ID="your-gcp-project-id"
CLUSTER_NAME="gsc-mainnet-cluster"
ZONE="us-central1-a"

echo "🚀 Deploying GSC Mainnet to GCP..."

# Create GKE cluster
gcloud container clusters create $CLUSTER_NAME \\
    --zone $ZONE \\
    --num-nodes 3 \\
    --machine-type e2-standard-2 \\
    --enable-autoscaling \\
    --min-nodes 1 \\
    --max-nodes 10

# Get cluster credentials
gcloud container clusters get-credentials $CLUSTER_NAME --zone $ZONE

# Build and push Docker image
docker build -t gcr.io/$PROJECT_ID/gsccoin/mainnet-node:latest .
docker push gcr.io/$PROJECT_ID/gsccoin/mainnet-node:latest

# Deploy to Kubernetes
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

echo "✅ Deployment complete!"
echo "📊 Check status: kubectl get pods,services,ingress"
"""
        
        with open('gcp_deploy/deploy.sh', 'w') as f:
            f.write(deploy_script)
        
        os.chmod('gcp_deploy/deploy.sh', 0o755)
        
        print("✅ GCP deployment configurations generated")
        print("📝 Next steps:")
        print("1. Set up GCP project and enable APIs")
        print("2. Configure gcloud CLI: gcloud auth login")
        print("3. Update PROJECT_ID in deploy.sh")
        print("4. Run: cd gcp_deploy && ./deploy.sh")
        
        return {
            'provider': 'gcp',
            'region': self.region,
            'configs_generated': True,
            'next_steps': 'Run deploy.sh script'
        }
    
    def deploy_azure(self, instance_count: int = 3) -> Dict:
        """Deploy to Microsoft Azure using Container Instances"""
        print("🚀 Deploying GSC Mainnet to Azure...")
        
        # Azure Resource Manager template
        arm_template = {
            "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
            "contentVersion": "1.0.0.0",
            "parameters": {
                "containerGroupName": {
                    "type": "string",
                    "defaultValue": f"{self.project_name}-group"
                },
                "location": {
                    "type": "string",
                    "defaultValue": self.region
                }
            },
            "resources": [
                {
                    "type": "Microsoft.ContainerInstance/containerGroups",
                    "apiVersion": "2021-03-01",
                    "name": "[parameters('containerGroupName')]",
                    "location": "[parameters('location')]",
                    "properties": {
                        "containers": [
                            {
                                "name": "gsc-seed-node",
                                "properties": {
                                    "image": self.image_name,
                                    "ports": [
                                        {"port": 8333, "protocol": "TCP"},
                                        {"port": 8334, "protocol": "TCP"},
                                        {"port": 8335, "protocol": "TCP"}
                                    ],
                                    "environmentVariables": [
                                        {"name": "GSC_NETWORK", "value": "mainnet"},
                                        {"name": "GSC_NODE_TYPE", "value": "seed"}
                                    ],
                                    "resources": {
                                        "requests": {"cpu": 1, "memoryInGB": 2}
                                    }
                                }
                            }
                        ],
                        "osType": "Linux",
                        "ipAddress": {
                            "type": "Public",
                            "ports": [
                                {"port": 8333, "protocol": "TCP"},
                                {"port": 8334, "protocol": "TCP"},
                                {"port": 8335, "protocol": "TCP"}
                            ],
                            "dnsNameLabel": f"{self.project_name}-seed"
                        },
                        "restartPolicy": "Always"
                    }
                }
            ],
            "outputs": {
                "containerIPv4Address": {
                    "type": "string",
                    "value": "[reference(resourceId('Microsoft.ContainerInstance/containerGroups', parameters('containerGroupName'))).ipAddress.ip]"
                }
            }
        }
        
        # Save configurations
        os.makedirs('azure_deploy', exist_ok=True)
        
        with open('azure_deploy/arm_template.json', 'w') as f:
            json.dump(arm_template, f, indent=2)
        
        # Generate deployment script
        deploy_script = f"""#!/bin/bash
# Azure Deployment Script for GSC Mainnet

set -e

RESOURCE_GROUP="gsc-mainnet-rg"
LOCATION="{self.region}"
TEMPLATE_FILE="arm_template.json"

echo "🚀 Deploying GSC Mainnet to Azure..."

# Create resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Deploy ARM template
az deployment group create \\
    --resource-group $RESOURCE_GROUP \\
    --template-file $TEMPLATE_FILE \\
    --parameters containerGroupName=gsc-mainnet-group

echo "✅ Deployment complete!"
echo "📊 Check status: az container show --resource-group $RESOURCE_GROUP --name gsc-mainnet-group"
"""
        
        with open('azure_deploy/deploy.sh', 'w') as f:
            f.write(deploy_script)
        
        os.chmod('azure_deploy/deploy.sh', 0o755)
        
        print("✅ Azure deployment configurations generated")
        print("📝 Next steps:")
        print("1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        print("2. Login: az login")
        print("3. Run: cd azure_deploy && ./deploy.sh")
        
        return {
            'provider': 'azure',
            'region': self.region,
            'configs_generated': True,
            'next_steps': 'Run deploy.sh script'
        }
    
    def deploy(self, instance_count: int = 3) -> Dict:
        """Deploy to the specified cloud provider"""
        if self.provider == 'aws':
            return self.deploy_aws(instance_count)
        elif self.provider == 'gcp':
            return self.deploy_gcp(instance_count)
        elif self.provider == 'azure':
            return self.deploy_azure(instance_count)
        else:
            raise ValueError(f"Unsupported cloud provider: {self.provider}")

def main():
    parser = argparse.ArgumentParser(description='Deploy GSC Mainnet to Cloud')
    parser.add_argument('provider', choices=['aws', 'gcp', 'azure'], help='Cloud provider')
    parser.add_argument('--region', help='Deployment region')
    parser.add_argument('--instances', type=int, default=3, help='Number of instances')
    
    args = parser.parse_args()
    
    deployer = CloudDeployer(args.provider, args.region)
    result = deployer.deploy(args.instances)
    
    print(f"\n🎉 Deployment configuration complete!")
    print(f"Provider: {result['provider']}")
    print(f"Region: {result['region']}")
    print(f"Status: {result['next_steps']}")

if __name__ == '__main__':
    main()
