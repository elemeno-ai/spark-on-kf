#!/usr/bin/env just --justfile

MINIKUBE_VERSION := "1.23.2"
MINIKUBE_MEMORY_MB := "16384"
MINIKUBE_CPU := "6"

PIPELINE_VERSION := "1.8.1"

############################

install-minikube:
    minikube start  --memory {{MINIKUBE_MEMORY_MB}} --cpus {{MINIKUBE_CPU}} --insecure-registry "10.0.0.0/24" --container-runtime=docker --kubernetes-version=v{{MINIKUBE_VERSION}}
    minikube addons enable metrics-server
    minikube addons enable registry

install-kubeflow:
    kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/cluster-scoped-resources?ref={{PIPELINE_VERSION}}"
    kubectl wait --for condition=established --timeout=60s crd/applications.app.k8s.io
    kubectl apply -k "github.com/kubeflow/pipelines/manifests/kustomize/env/platform-agnostic-pns?ref={{PIPELINE_VERSION}}" && \
    kubectl rollout status -n kubeflow deployment/ml-pipeline -w

install-spark:
    helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator
    helm install sparkop spark-operator/spark-operator --namespace kubeflow --create-namespace

install-spark-rbac:
    kubectl apply -f ./k8s/spark-rbac.yaml

#############################

connect:
    kubectl ctx minikube

expose:
    kubectl port-forward -n kubeflow svc/ml-pipeline-ui 8005:80

run-pipeline:
    python3 pipeline.py