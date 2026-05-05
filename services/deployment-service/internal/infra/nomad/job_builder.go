package nomad

import (
	"bytes"
	_ "embed"
	"fmt"
	"strings"
	"text/template"

	"deployment-service/internal/app/port"
	"deployment-service/internal/app/usecase/command"
)

//go:embed templates/build_job.hcl.tmpl
var buildJobTmpl string

//go:embed templates/deploy_job.hcl.tmpl
var deployJobTmpl string

type JobBuilder struct {
	buildTmpl  *template.Template
	deployTmpl *template.Template
}

func NewJobBuilder() *JobBuilder {
	return &JobBuilder{
		buildTmpl:  template.Must(template.New("build").Parse(buildJobTmpl)),
		deployTmpl: template.Must(template.New("deploy").Parse(deployJobTmpl)),
	}
}

func (b *JobBuilder) RenderBuildJob(p command.BuildJobParams) (string, error) {
	cloneURL := p.GitHubRepoURL
	if p.GitHubToken != "" && strings.Contains(cloneURL, "github.com") {
		cloneURL = strings.Replace(cloneURL, "https://github.com", "https://"+p.GitHubToken+"@github.com", 1)
	}

	script := fmt.Sprintf(
		"echo %s | docker login %s -u %s --password-stdin && apk add --no-cache git && git clone %s repo && cd repo && docker build -t %s -f %s %s && docker push %s",
		shellEscape(p.RegistryPassword),
		p.RegistryURL,
		shellEscape(p.RegistryUser),
		cloneURL,
		p.ImageTag,
		p.DockerfilePath,
		p.BuildContext,
		p.ImageTag,
	)

	data := struct {
		ProjectID   string
		Version     string
		BuildScript string
	}{
		ProjectID:   p.ProjectID,
		Version:     p.Version,
		BuildScript: script,
	}

	var buf bytes.Buffer
	if err := b.buildTmpl.Execute(&buf, data); err != nil {
		return "", fmt.Errorf("render build job template: %w", err)
	}
	return buf.String(), nil
}

func (b *JobBuilder) RenderDeployJob(p command.DeployJobParams) (string, error) {
	data := struct {
		DeploymentID     string
		ProjectID        string
		ImageURL         string
		Port             int
		StartCommand     string
		RegistryURL      string
		RegistryUser     string
		RegistryPassword string
		Hostname         string
		VaultTemplate    string
	}{
		DeploymentID:     p.DeploymentID,
		ProjectID:        p.ProjectID,
		ImageURL:         p.ImageURL,
		Port:             p.Port,
		StartCommand:     p.StartCommand,
		RegistryURL:      p.RegistryURL,
		RegistryUser:     p.RegistryUser,
		RegistryPassword: p.RegistryPassword,
		Hostname:         p.Hostname,
		VaultTemplate:    buildVaultTemplate(p.Secrets),
	}

	var buf bytes.Buffer
	if err := b.deployTmpl.Execute(&buf, data); err != nil {
		return "", fmt.Errorf("render deploy job template: %w", err)
	}
	return buf.String(), nil
}

func buildVaultTemplate(secrets []port.SecretRef) string {
	if len(secrets) == 0 {
		return ""
	}
	vaultPath := secrets[0].VaultPath
	var sb strings.Builder
	fmt.Fprintf(&sb, `{{ with secret "secret/data/%s" }}`+"\n", vaultPath)
	for _, s := range secrets {
		fmt.Fprintf(&sb, `%s="{{ .Data.data.%s }}"`+"\n", s.Key, s.Key)
	}
	sb.WriteString(`{{ end }}`)
	return sb.String()
}

func shellEscape(s string) string {
	return "'" + strings.ReplaceAll(s, "'", `'\''`) + "'"
}
