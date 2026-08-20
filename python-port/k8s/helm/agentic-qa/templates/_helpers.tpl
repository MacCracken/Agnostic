{{- /*
Expand the name of the chart.
*/}}
{{- define "agentic-qa.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- /*
Create a default fully qualified app name.
*/}}
{{- define "agentic-qa.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{- /*
Create chart name and version as used by the chart label.
*/}}
{{- define "agentic-qa.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- /*
Common labels
*/}}
{{- define "agentic-qa.labels" -}}
helm.sh/chart: {{ include "agentic-qa.chart" . }}
{{ include "agentic-qa.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- with .Values.commonLabels }}
{{ toYaml . }}
{{- end }}
{{- end }}

{{- /*
Selector labels
*/}}
{{- define "agentic-qa.selectorLabels" -}}
app.kubernetes.io/name: {{ include "agentic-qa.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{- /*
Create the name of the service account to use
*/}}
{{- define "agentic-qa.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "agentic-qa.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{- /*
Create image name
*/}}
{{- define "agentic-qa.image" -}}
{{- $registry := .Values.global.imageRegistry | default .Values.image.registry -}}
{{- if .Values.global }}
{{- $repository := .Values.global.imageRepository | default .Values.image.repository -}}
{{- if .Values.global.tag }}
{{- printf "%s/%s:%s" $registry $repository .Values.global.tag -}}
{{- else }}
{{- printf "%s/%s:%s" $registry $repository (.Values.image.tag | default .Chart.AppVersion) -}}
{{- end }}
{{- else }}
{{- printf "%s/%s:%s" $registry .Values.image.repository (.Values.image.tag | default .Chart.AppVersion) -}}
{{- end }}
{{- end }}