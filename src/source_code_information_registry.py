import os

from enum import Enum

from .logger import Logger

class SourceCodeInformationRegistry:
    logger = Logger.get_logger("SourceCodeInformationRegistry")

    # TODO: Expand by more connection approaches in the future
    class SourceCodeLocationType(Enum):
        LOCALHOST = 1
        REMOTE_REACHED_VIA_SSH = 2
    
    # Expects an absolute path for source code location in the filesystem
    def __init__(self, source_code_location_type: SourceCodeLocationType, source_code_location: str):
        self.file_structure = ...
        
        if source_code_location_type == self.SourceCodeLocationType.LOCALHOST:
            self._build_source_code_info_from_local(source_code_location)
        elif source_code_location_type == self.SourceCodeLocationType.REMOTE_REACHED_VIA_SSH:
            self._build_source_code_info_with_ssh(source_code_location)
        else:
            raise ValueError(f"Invalid source code location type: {source_code_location_type}")
        
    def _build_source_code_info_from_local_without_jdbtarget(self, source_code_location: str) -> None:
        ...    

    def _build_source_code_info_from_local(self, source_code_location: str) -> None:
        if not os.path.exists(os.path.join(source_code_location, ".jdbtarget")):
            self.logger.warning(
                f"Did not find a .jdbtarget file at {source_code_location}, " +
                "will search the whole directory except for git worktrees"
            )
            self._build_source_code_info_from_local_without_jdbtarget(source_code_location)

        with open(os.path.join(source_code_location, ".jdbtarget"))    



    def _build_source_code_info_with_ssh(self, source_code_location: str) -> None:
        self._validate_remote_source_code_location(source_code_location)
        ip_address, filepath = source_code_location.split(sep=":")   

    def __validate_remote_source_code_location(self, remote_source_code_loation: str) -> None:
        ...    