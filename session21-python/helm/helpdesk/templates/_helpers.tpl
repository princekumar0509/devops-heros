{{- define "helpdesk.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "helpdesk.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/part-of: helpdesk
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Usage: include "helpdesk.selectorLabels" (dict "ctx" . "component" "backend") */}}
{{- define "helpdesk.selectorLabels" -}}
app.kubernetes.io/name: {{ .ctx.Chart.Name }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "helpdesk.backendName" -}}{{ include "helpdesk.fullname" . }}-backend{{- end -}}
{{- define "helpdesk.frontendName" -}}{{ include "helpdesk.fullname" . }}-frontend{{- end -}}
{{- define "helpdesk.postgresName" -}}{{ include "helpdesk.fullname" . }}-postgres{{- end -}}

{{/* Reuse the existing password on upgrade so the database keeps working. */}}
{{- define "helpdesk.postgresPassword" -}}
{{- if .Values.postgres.password -}}
{{- .Values.postgres.password -}}
{{- else -}}
{{- $existing := lookup "v1" "Secret" .Release.Namespace (include "helpdesk.postgresName" .) -}}
{{- if and $existing $existing.data (index $existing.data "password") -}}
{{- index $existing.data "password" | b64dec -}}
{{- else -}}
{{- randAlphaNum 24 -}}
{{- end -}}
{{- end -}}
{{- end -}}

{{- define "helpdesk.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "helpdesk.containerSecurityContext" -}}
allowPrivilegeEscalation: false
capabilities:
  drop: [ALL]
{{- end -}}
