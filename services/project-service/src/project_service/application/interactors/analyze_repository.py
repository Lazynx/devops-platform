import json
import logging
from dataclasses import asdict

from project_service.application.dtos import (
    AnalyzeRepositoryInputDTO,
    AnalyzeRepositoryOutputDTO,
    RepositoryConfigDTO,
    RepositoryFileDTO,
)
from project_service.application.interfaces.auth_service import IAuthService
from project_service.application.interfaces.github_service import IGitHubService

logger = logging.getLogger(__name__)


class AnalyzeRepositoryInteractor:
    def __init__(
        self,
        auth_service: IAuthService,
        github_service: IGitHubService,
    ):
        self._auth_service = auth_service
        self._github_service = github_service

    async def __call__(self, dto: AnalyzeRepositoryInputDTO) -> AnalyzeRepositoryOutputDTO:
        github_token = await self._auth_service.get_github_token(dto.user_access_token)

        repo_files = await self._github_service.get_repo_contents(
            github_token,
            dto.owner,
            dto.repo,
            path=dto.root_directory
        )

        config = await self._analyze_repository(
            repo_files,
            dto.owner,
            dto.repo,
            github_token,
            dto.root_directory
        )

        return AnalyzeRepositoryOutputDTO(**asdict(config))

    async def _analyze_repository(
        self,
        files: list[RepositoryFileDTO],
        owner: str,
        repo: str,
        github_token: str,
        root_directory: str
    ) -> RepositoryConfigDTO:
        file_names = {file.name for file in files if file.type == 'file'}

        # Node.js / JavaScript / TypeScript
        if 'package.json' in file_names:
            result = await self._detect_nodejs_framework(
                file_names, owner, repo, github_token, root_directory
            )
            if result:
                return result

        # Python
        if 'requirements.txt' in file_names or 'pyproject.toml' in file_names:
            result = await self._detect_python_framework(
                file_names, owner, repo, github_token, root_directory
            )
            if result:
                return result

        # Go
        if 'go.mod' in file_names:
            return self._create_config(
                repository=f'{owner}/{repo}',
                root_directory=root_directory,
                framework='Go',
                confidence='high',
                install_command='go mod download',
                build_command='go build',
                start_command='go run .',
                detected_files=['go.mod']
            )

        # Rust
        if 'Cargo.toml' in file_names:
            return self._create_config(
                repository=f'{owner}/{repo}',
                root_directory=root_directory,
                framework='Rust',
                confidence='high',
                install_command='cargo fetch',
                build_command='cargo build --release',
                start_command='cargo run',
                detected_files=['Cargo.toml']
            )

        # Java (Maven)
        if 'pom.xml' in file_names:
            return self._create_config(
                repository=f'{owner}/{repo}',
                root_directory=root_directory,
                framework='Java (Maven)',
                confidence='high',
                install_command='mvn install',
                build_command='mvn clean package',
                start_command='mvn spring-boot:run',
                detected_files=['pom.xml']
            )

        # Java (Gradle)
        if 'build.gradle' in file_names or 'build.gradle.kts' in file_names:
            gradle_file = 'build.gradle.kts' if 'build.gradle.kts' in file_names else 'build.gradle'
            return self._create_config(
                repository=f'{owner}/{repo}',
                root_directory=root_directory,
                framework='Java (Gradle)',
                confidence='high',
                install_command='./gradlew dependencies',
                build_command='./gradlew build',
                start_command='./gradlew bootRun',
                detected_files=[gradle_file]
            )

        # Unknown framework
        return self._create_config(
            repository=f'{owner}/{repo}',
            root_directory=root_directory,
            framework='Unknown',
            confidence='low',
            install_command=None,
            build_command=None,
            start_command=None,
            detected_files=[]
        )

    async def _detect_nodejs_framework(
        self,
        file_names: set[str],
        owner: str,
        repo: str,
        github_token: str,
        root_directory: str
    ) -> RepositoryConfigDTO | None:
        detected = ['package.json']
        framework = 'Node.js'
        confidence = 'medium'
        install_cmd = 'npm install'
        build_cmd = 'npm run build'
        start_cmd = 'npm start'

        file_path = self._build_file_path(root_directory, 'package.json')
        package_json = await self._github_service.get_file_content(github_token, owner, repo, file_path)

        if not package_json:
            return None

        try:
            package_data = json.loads(package_json)
            dependencies = package_data.get('dependencies', {})
            dev_dependencies = package_data.get('devDependencies', {})
            all_deps = {**dependencies, **dev_dependencies}

            # Next.js
            if 'next' in all_deps:
                framework = 'Next.js'
                confidence = 'high'
                build_cmd = 'npm run build'
                start_cmd = 'npm run dev'
                if 'next.config.js' in file_names or 'next.config.mjs' in file_names:
                    detected.append('next.config.js' if 'next.config.js' in file_names else 'next.config.mjs')

            # Vite
            elif 'vite' in all_deps:
                if 'react' in all_deps:
                    framework = 'React (Vite)'
                elif 'vue' in all_deps:
                    framework = 'Vue (Vite)'
                elif 'svelte' in all_deps:
                    framework = 'Svelte (Vite)'
                else:
                    framework = 'Vite'
                confidence = 'high'
                build_cmd = 'npm run build'
                start_cmd = 'npm run dev'
                if 'vite.config.js' in file_names or 'vite.config.ts' in file_names:
                    detected.append('vite.config.js' if 'vite.config.js' in file_names else 'vite.config.ts')

            # Create React App
            elif 'react-scripts' in all_deps:
                framework = 'React (CRA)'
                confidence = 'high'
                build_cmd = 'npm run build'
                start_cmd = 'npm start'

            # React (generic)
            elif 'react' in all_deps:
                framework = 'React'
                confidence = 'medium'

            # Angular
            elif '@angular/core' in all_deps:
                framework = 'Angular'
                confidence = 'high'
                build_cmd = 'npm run build'
                start_cmd = 'ng serve'
                if 'angular.json' in file_names:
                    detected.append('angular.json')

            # Vue.js
            elif 'vue' in all_deps:
                framework = 'Vue.js'
                confidence = 'high'
                build_cmd = 'npm run build'
                start_cmd = 'npm run serve'
                if 'vue.config.js' in file_names:
                    detected.append('vue.config.js')

            # NestJS
            elif '@nestjs/core' in all_deps:
                framework = 'NestJS'
                confidence = 'high'
                build_cmd = 'npm run build'
                start_cmd = 'npm run start:dev'

            # Express
            elif 'express' in all_deps:
                framework = 'Express'
                confidence = 'high'
                build_cmd = None
                start_cmd = 'npm start'

            return self._create_config(
                repository=f'{owner}/{repo}',
                root_directory=root_directory,
                framework=framework,
                confidence=confidence,
                install_command=install_cmd,
                build_command=build_cmd,
                start_command=start_cmd,
                detected_files=detected
            )

        except json.JSONDecodeError:
            logger.error(f'Failed to parse package.json for {owner}/{repo}')
            return None

    async def _detect_python_framework(
        self,
        file_names: set[str],
        owner: str,
        repo: str,
        github_token: str,
        root_directory: str
    ) -> RepositoryConfigDTO | None:
        detected = []
        framework = 'Python'
        confidence = 'medium'
        install_cmd = 'pip install -r requirements.txt'
        build_cmd = None  # Python doesn't need build step
        start_cmd = 'python main.py'

        dependencies = set()

        # Parse requirements.txt
        if 'requirements.txt' in file_names:
            file_path = self._build_file_path(root_directory, 'requirements.txt')
            requirements = await self._github_service.get_file_content(github_token, owner, repo, file_path)
            if requirements:
                detected.append('requirements.txt')
                for line in requirements.split('\n'):
                    line = line.strip()
                    if line and not line.startswith('#'):
                        pkg = line.split('==')[0].split('>=')[0].split('<=')[0].split('~=')[0].strip().lower()
                        dependencies.add(pkg)

        # Parse pyproject.toml
        if 'pyproject.toml' in file_names:
            file_path = self._build_file_path(root_directory, 'pyproject.toml')
            pyproject = await self._github_service.get_file_content(github_token, owner, repo, file_path)
            if pyproject:
                detected.append('pyproject.toml')
                content_lower = pyproject.lower()
                if 'fastapi' in content_lower:
                    dependencies.add('fastapi')
                if 'django' in content_lower:
                    dependencies.add('django')
                if 'flask' in content_lower:
                    dependencies.add('flask')
                if 'requirements.txt' not in file_names:
                    install_cmd = 'pip install .'

        # FastAPI
        if 'fastapi' in dependencies:
            framework = 'FastAPI'
            confidence = 'high'
            if 'main.py' in file_names:
                start_cmd = 'uvicorn main:app --host 0.0.0.0 --port $PORT'
                detected.append('main.py')
            elif 'app.py' in file_names:
                start_cmd = 'uvicorn app:app --host 0.0.0.0 --port $PORT'
                detected.append('app.py')
            else:
                start_cmd = 'uvicorn main:app --host 0.0.0.0 --port $PORT'

        # Django
        elif 'django' in dependencies:
            framework = 'Django'
            confidence = 'high'
            start_cmd = 'python manage.py runserver 0.0.0.0:$PORT'
            if 'manage.py' in file_names:
                detected.append('manage.py')

        # Flask
        elif 'flask' in dependencies:
            framework = 'Flask'
            confidence = 'high'
            start_cmd = 'flask run --host=0.0.0.0 --port=$PORT'
            if 'app.py' in file_names:
                detected.append('app.py')
            elif 'wsgi.py' in file_names:
                detected.append('wsgi.py')

        # Django (detected by manage.py)
        elif 'manage.py' in file_names:
            framework = 'Django'
            confidence = 'medium'
            start_cmd = 'python manage.py runserver 0.0.0.0:$PORT'
            detected.append('manage.py')

        return self._create_config(
            repository=f'{owner}/{repo}',
            root_directory=root_directory,
            framework=framework,
            confidence=confidence,
            install_command=install_cmd,
            build_command=build_cmd,
            start_command=start_cmd,
            detected_files=detected
        )

    def _create_config(
        self,
        repository: str,
        root_directory: str,
        framework: str,
        confidence: str,
        install_command: str | None,
        build_command: str | None,
        start_command: str | None,
        detected_files: list[str]
    ) -> RepositoryConfigDTO:
        return RepositoryConfigDTO(
            repository=repository,
            root_directory=root_directory,
            framework=framework,
            confidence=confidence,
            install_command=install_command,
            build_command=build_command,
            start_command=start_command,
            detected_files=detected_files
        )

    @staticmethod
    def _build_file_path(root_directory: str, filename: str) -> str:
        normalized_root = root_directory.strip('./').strip('/')

        if normalized_root:
            return f'{normalized_root}/{filename}'
        return filename
