# Agentic QA Helm Chart

This directory contains the Helm chart for deploying the Agentic QA Team System to Kubernetes.

## Prerequisites

- Kubernetes cluster (v1.20+)
- Helm 3.x
- `kubectl` configured to connect to your cluster
- Sufficient resources (minimum 4 CPU, 8GB RAM)

## Quick Start

1. **Create namespace and set up secrets:**
   ```bash
   # Create namespace (if not using helm to create it)
   kubectl create namespace agentic-qa
   
   # Set your OpenAI API key (base64 encoded)
   echo -n "your-openai-api-key" | base64
   # Copy the output and update the secrets.yaml file
   ```

2. **Install the chart:**
   ```bash
   # Install with default values
   helm install agentic-qa ./k8s/helm/agentic-qa --namespace agentic-qa
   
   # Install with custom values
   helm install agentic-qa ./k8s/helm/agentic-qa \
     --namespace agentic-qa \
     --set secrets.openaiApiKey=$(echo -n "your-openai-key" | base64) \
     --set ingress.enabled=true \
     --set ingress.host=qa.yourdomain.com
   ```

3. **Verify deployment:**
   ```bash
   # Check pod status
   kubectl get pods -n agentic-qa
   
   # Check services
   kubectl get services -n agentic-qa
   
   # Check webgui access
   kubectl port-forward service/webgui-service 8000:8000 -n agentic-qa
   ```

## Configuration

Key configuration options in `values.yaml`:

- **Infrastructure**: Enable/disable Redis and RabbitMQ
- **Agents**: Configure which QA agents to deploy and their resource limits
- **WebGUI**: Frontend service configuration
- **Ingress**: External access configuration
- **Resources**: CPU and memory limits for each component
- **Autoscaling**: Horizontal pod autoscaling settings

## Scaling

You can scale individual agents:

```bash
# Scale junior QA workers
helm upgrade agentic-qa ./k8s/helm/agentic-qa \
  --namespace agentic-qa \
  --set agents.juniorQa.replicaCount=3

# Enable autoscaling
helm upgrade agentic-qa ./k8s/helm/agentic-qa \
  --namespace agentic-qa \
  --set autoscaling.enabled=true
```

## Monitoring

- Check logs: `kubectl logs -f deployment/webgui -n agentic-qa`
- Monitor resource usage: `kubectl top pods -n agentic-qa`
- Access RabbitMQ management: `kubectl port-forward service/rabbitmq-service 15672:15672 -n agentic-qa`

## Uninstall

```bash
helm uninstall agentic-qa --namespace agentic-qa
```

## Troubleshooting

1. **Pods not starting**: Check resource limits and node availability
2. **Connection issues**: Verify service names and network policies
3. **Secret errors**: Ensure OpenAI API key is properly base64 encoded

For more details, see the main documentation.