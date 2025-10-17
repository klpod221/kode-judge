"""
Utility for filtering fields in response data.
"""

from typing import Dict, Any, List, Set


class FieldFilter:
    """Handles filtering of fields in submission responses."""
    
    # Default fields to return when fields parameter is empty/null
    DEFAULT_FIELDS = {
        "id",
        "status",
        "language_id",
        "stdout",
        "stderr",
        "stdin",
        "compile_output",
        "created_at",
    }
    
    # All available fields
    ALL_FIELDS = {
        "id",
        "source_code",
        "language_id",
        "stdin",
        "additional_files",
        "expected_output",
        "cpu_time_limit",
        "cpu_extra_time",
        "wall_time_limit",
        "memory_limit",
        "max_processes_and_or_threads",
        "max_file_size",
        "number_of_runs",
        "enable_per_process_and_thread_time_limit",
        "enable_per_process_and_thread_memory_limit",
        "redirect_stderr_to_stdout",
        "enable_network",
        "language",
        "status",
        "stdout",
        "stderr",
        "compile_output",
        "meta",
        "created_at",
    }
    
    @staticmethod
    def parse_fields(fields: str | None) -> Set[str] | None:
        """
        Parses fields parameter string into a set of field names.
        
        Args:
            fields: Comma-separated field names, 'all', or 'default' with additional fields.
            
        Returns:
            Set[str] | None: Set of field names, None for default fields, or all fields.
            
        Examples:
            - None or "" -> None (uses DEFAULT_FIELDS)
            - "all" -> ALL_FIELDS
            - "stdout,stderr" -> {"id", "stdout", "stderr"}
            - "default,meta,additional_files" -> DEFAULT_FIELDS + {"meta", "additional_files"}
        """
        if not fields or fields.strip() == "":
            return None
        
        if fields.strip().lower() == "all":
            return FieldFilter.ALL_FIELDS.copy()
        
        # Parse comma-separated fields
        requested_fields = {f.strip().lower() for f in fields.split(",") if f.strip()}
        
        # Check if "default" is in the requested fields
        if "default" in requested_fields:
            # Remove "default" from the set and start with DEFAULT_FIELDS
            requested_fields.remove("default")
            result_fields = FieldFilter.DEFAULT_FIELDS.copy()
            # Add additional requested fields
            result_fields.update(requested_fields)
        else:
            # No "default" keyword, just use requested fields
            result_fields = requested_fields
            # Always include id field for reference
            result_fields.add("id")
        
        # Validate fields - only keep valid ones
        valid_fields = result_fields & FieldFilter.ALL_FIELDS
        
        return valid_fields if valid_fields else None
    
    @staticmethod
    def filter_data(data: Dict[str, Any], fields: Set[str] | None) -> Dict[str, Any]:
        """
        Filters dictionary data to include only specified fields.
        
        Args:
            data: Original data dictionary.
            fields: Set of field names to include, or None for defaults.
            
        Returns:
            Dict[str, Any]: Filtered data dictionary.
        """
        if fields is None:
            fields = FieldFilter.DEFAULT_FIELDS
        
        return {k: v for k, v in data.items() if k in fields}
    
    @staticmethod
    def filter_list(
        data_list: List[Dict[str, Any]], fields: Set[str] | None
    ) -> List[Dict[str, Any]]:
        """
        Filters a list of dictionaries to include only specified fields.
        
        Args:
            data_list: List of data dictionaries.
            fields: Set of field names to include, or None for defaults.
            
        Returns:
            List[Dict[str, Any]]: List of filtered data dictionaries.
        """
        return [FieldFilter.filter_data(data, fields) for data in data_list]
