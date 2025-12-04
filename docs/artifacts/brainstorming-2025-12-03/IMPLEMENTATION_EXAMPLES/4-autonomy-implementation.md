# 4. AUTONOMY IMPLEMENTATION

### 4.1 Parallel Property Processing

```python
# src/phx_home_analysis/pipeline/parallel_orchestrator.py

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
import logging


@dataclass
class PropertyProcessingResult:
    """Result of processing a single property."""
    address: str
    status: str  # "completed", "failed", "blocked"
    phases_completed: list[str]
    phases_failed: list[str]
    error_message: str | None = None
    duration_seconds: float = 0.0


class ParallelPropertyOrchestrator:
    """Process multiple properties in parallel with dependency awareness."""

    def __init__(
        self,
        phase_dag: PhaseDAG,
        max_parallel_properties: int = 3,
        max_parallel_phases: int = 2
    ):
        self.phase_dag = phase_dag
        self.max_parallel_properties = max_parallel_properties
        self.max_parallel_phases = max_parallel_phases
        self.logger = logging.getLogger(__name__)

    def process_all_properties(
        self,
        properties: list[Property]
    ) -> list[PropertyProcessingResult]:
        """Process all properties in parallel."""
        results = []

        with ThreadPoolExecutor(max_workers=self.max_parallel_properties) as executor:
            futures = {
                executor.submit(self.process_single_property, prop): prop
                for prop in properties
            }

            for future in as_completed(futures):
                prop = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    self.logger.info(
                        f"Property {prop.full_address}: {result.status} "
                        f"({result.duration_seconds:.2f}s)"
                    )
                except Exception as e:
                    self.logger.error(
                        f"Processing {prop.full_address} failed: {e}",
                        exc_info=True
                    )
                    results.append(PropertyProcessingResult(
                        address=prop.full_address,
                        status="failed",
                        phases_completed=[],
                        phases_failed=[],
                        error_message=str(e)
                    ))

        return results

    def process_single_property(self, property: Property) -> PropertyProcessingResult:
        """Process a single property through all phases."""
        import time
        start_time = time.time()

        phases_completed = []
        phases_failed = []
        work_item = WorkItem(address=property.full_address)

        # Process phases in order
        for phase_group in self.phase_dag.execution_order:
            # Check if all dependencies are met
            completed_set = set(phases_completed)

            # Execute phases in group in parallel (if applicable)
            with ThreadPoolExecutor(max_workers=self.max_parallel_phases) as executor:
                futures = {}

                for phase_id in phase_group:
                    phase = self.phase_dag.get_phase(phase_id)

                    # Check if phase is blocked
                    if phase.is_blocked_by(completed_set):
                        self.logger.debug(f"{phase_id}: blocked by dependencies")
                        continue

                    # Check if phase was already completed
                    if work_item.is_phase_completed(phase_id):
                        self.logger.debug(f"{phase_id}: already completed (resuming)")
                        phases_completed.append(phase_id)
                        continue

                    # Submit phase execution
                    future = executor.submit(
                        self._execute_phase,
                        property,
                        phase,
                        work_item
                    )
                    futures[future] = phase_id

                # Wait for parallel phases to complete
                for future in as_completed(futures):
                    phase_id = futures[future]
                    try:
                        success = future.result()
                        if success:
                            phases_completed.append(phase_id)
                            work_item.mark_phase_completed(phase_id)
                        else:
                            phases_failed.append(phase_id)
                    except Exception as e:
                        self.logger.error(f"{phase_id} failed: {e}")
                        phases_failed.append(phase_id)

        duration = time.time() - start_time
        status = "completed" if not phases_failed else "failed"

        return PropertyProcessingResult(
            address=property.full_address,
            status=status,
            phases_completed=phases_completed,
            phases_failed=phases_failed,
            duration_seconds=duration
        )

    def _execute_phase(
        self,
        property: Property,
        phase: Phase,
        work_item: WorkItem
    ) -> bool:
        """Execute a single phase for a property."""
        import time

        max_attempts = phase.max_retries
        attempt = 0
        last_error = None

        while attempt < max_attempts:
            try:
                # Validate prerequisites if needed
                if phase.prerequisite_validation:
                    can_spawn = self._validate_prerequisites(
                        property,
                        phase.prerequisite_validation
                    )
                    if not can_spawn:
                        self.logger.warning(
                            f"{phase.id}: prerequisites not met for {property.full_address}"
                        )
                        work_item.mark_phase_skipped(phase.id)
                        return False

                # Execute phase
                self.logger.info(f"Starting {phase.id} for {property.full_address}")

                if phase.executor_type == ExecutorType.SCRIPT:
                    self._execute_script_phase(property, phase)
                elif phase.executor_type == ExecutorType.AGENT:
                    self._execute_agent_phase(property, phase)

                self.logger.info(f"Completed {phase.id} for {property.full_address}")
                return True

            except Exception as e:
                attempt += 1
                last_error = e

                if attempt < max_attempts and phase.retryable:
                    wait_time = phase.backoff_factor ** (attempt - 1)
                    self.logger.warning(
                        f"{phase.id} attempt {attempt} failed: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    time.sleep(wait_time)
                else:
                    self.logger.error(
                        f"{phase.id} failed after {attempt} attempts: {e}"
                    )

        return False

    def _validate_prerequisites(
        self,
        property: Property,
        validation_script: str
    ) -> bool:
        """Validate phase prerequisites."""
        # Implement by calling validate_phase_prerequisites.py
        pass

    def _execute_script_phase(self, property: Property, phase: Phase) -> None:
        """Execute a script-based phase."""
        # Implement by running Python script
        pass

    def _execute_agent_phase(self, property: Property, phase: Phase) -> None:
        """Execute an agent-based phase."""
        # Implement by spawning Task with agent
        pass
```

---
