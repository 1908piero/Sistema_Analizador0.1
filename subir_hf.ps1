$ErrorActionPreference = "Stop"
$repo = "https://huggingface.co/spaces/sooypiero1908/analizador-encuestas"
$dir = "analizador-encuestas"

Write-Host "1. Clonando el repositorio..."
Remove-Item $dir -Recurse -Force -ErrorAction SilentlyContinue
git clone $repo

Write-Host "2. Copiando archivos..."
Remove-Item "$dir\webapp" -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path "$dir\webapp" -Force | Out-Null
Copy-Item webapp\* "$dir\webapp\" -Recurse -Force
Copy-Item model $dir\model\ -Recurse -Force
Copy-Item export $dir\export\ -Recurse -Force
Copy-Item controller $dir\controller\ -Recurse -Force
Copy-Item i18n $dir\i18n\ -Recurse -Force
Copy-Item webapp\Dockerfile $dir\Dockerfile -Force

Write-Host "3. Subiendo a Hugging Face..."
Set-Location $dir
git add .
git commit -m "subir app completa"
git push

Write-Host "`nLISTO! Espera 3-5 min y abre:"
Write-Host "https://sooypiero1908-analizador-encuestas.hf.space"
Pause
