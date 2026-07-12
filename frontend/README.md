# Frontend — TáEmDia (Angular)

O aplicativo Angular será **gerado no Sprint 0**, depois que o Docker Desktop estiver instalado,
com o comando (rodado dentro de um container Node, para você não precisar instalar o Node):

```bash
docker run --rm -v "%cd%":/app -w /app node:20 npx -y @angular/cli@17 new taemdia-web \
  --directory . --style=scss --routing --skip-git
```

Depois adicionamos o Angular Material:
```bash
docker run --rm -v "%cd%":/app -w /app node:20 npx -y @angular/cli@17 add @angular/material
```

Enquanto isso, esta pasta fica reservada para a interface. O serviço `frontend` do
`docker-compose.yml` está comentado e será habilitado quando o app existir.
