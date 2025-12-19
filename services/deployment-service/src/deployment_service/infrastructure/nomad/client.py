import logging
import httpx
from typing import Any

logger = logging.getLogger(__name__)

class NomadClient:
    def __init__(self, url: str):
        self._url = url.rstrip('/')
        self._client = httpx.AsyncClient(timeout=30.0)

    async def create_job(self, job_hcl: str) -> dict[str, Any]:
        try:
            parse_response = await self._client.post(
                f"{self._url}/v1/jobs/parse",
                json={"JobHCL": job_hcl, "Canonicalize": True}
            )
            parse_response.raise_for_status()
            job_json = parse_response.json()

            job_id = job_json['ID']
            response = await self._client.post(
                f"{self._url}/v1/jobs",
                json={"Job": job_json}
            )
            response.raise_for_status()
            logger.info(f"Successfully submitted Nomad job: {job_id}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create Nomad job: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Response: {e.response.text}")
            raise

    async def get_job_allocations(self, job_id: str) -> list[dict[str, Any]]:
        try:
            response = await self._client.get(f"{self._url}/v1/job/{job_id}/allocations")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to get allocations for job {job_id}: {e}")
            raise

    async def wait_for_job_completion(self, job_id: str, timeout: int = 600, interval: int = 5) -> bool:
        import asyncio
        start_time = asyncio.get_event_loop().time()
        
        while True:
            if asyncio.get_event_loop().time() - start_time > timeout:
                logger.error(f"Timeout waiting for job {job_id}")
                return False

            try:
                allocations = await self.get_job_allocations(job_id)
                if not allocations:
                    await asyncio.sleep(interval)
                    continue

                allocations.sort(key=lambda x: x['CreateTime'], reverse=True)
                latest_alloc = allocations[0]
                
                client_status = latest_alloc['ClientStatus']
                
                if client_status == 'complete':
                    task_states = latest_alloc.get('TaskStates', {})
                    for task_name, state in task_states.items():
                        if state.get('State') == 'dead':
                             exit_code = state.get('Events', [{}])[-1].get('ExitCode')
                             if exit_code == 0:
                                 logger.info(f"Job {job_id} completed successfully")
                                 return True
                             else:
                                 logger.error(f"Job {job_id} failed with exit code {exit_code}")
                                 return False
                elif client_status == 'failed':
                    logger.error(f"Job {job_id} failed (ClientStatus: failed)")
                    return False
                
            except Exception as e:
                logger.warning(f"Error checking job status: {e}")
            
            await asyncio.sleep(interval)

    async def get_job_logs(self, job_id: str, task_name: str = "app", log_type: str = "stdout", tail: int = 100) -> str:
        try:
            allocations = await self.get_job_allocations(job_id)
            if not allocations:
                return f"No allocations found for job {job_id}"

            allocations.sort(key=lambda x: x['CreateTime'], reverse=True)
            latest_alloc = allocations[0]
            alloc_id = latest_alloc['ID']

            response = await self._client.get(
                f"{self._url}/v1/client/fs/logs/{alloc_id}",
                params={
                    "task": task_name,
                    "type": log_type,
                    "plain": "true",
                    "origin": "end",
                    "offset": tail * 1000,
                }
            )
            
            if response.status_code == 200:
                return response.text
            else:
                stderr_response = await self._client.get(
                    f"{self._url}/v1/client/fs/logs/{alloc_id}",
                    params={
                        "task": task_name,
                        "type": "stderr",
                        "plain": "true",
                        "origin": "end",
                        "offset": tail * 1000,
                    }
                )
                return f"STDOUT:\n{response.text}\n\nSTDERR:\n{stderr_response.text}"
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to get logs for job {job_id}: {e}")
            return f"Failed to get logs: {str(e)}"

    async def stop_job(self, job_id: str, purge: bool = True) -> None:
        try:
            response = await self._client.delete(
                f"{self._url}/v1/job/{job_id}",
                params={"purge": str(purge).lower()}
            )
            if response.status_code == 404:
                logger.warning(f"Job {job_id} not found when trying to stop")
                return
            response.raise_for_status()
            logger.info(f"Successfully stopped Nomad job: {job_id}")
        except httpx.HTTPError as e:
            logger.error(f"Failed to stop Nomad job {job_id}: {e}")
            raise

    async def close(self):
        await self._client.aclose()
