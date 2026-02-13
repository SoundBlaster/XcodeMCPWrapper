## REVIEW REPORT — FU-P9-T2-2 stale uvx troubleshooting docs

**Scope:** origin/main..HEAD
**Files:** 8

### Summary Verdict
- [x] Approve
- [ ] Approve with comments
- [ ] Request changes
- [ ] Block

### Critical Issues
- None.

### Secondary Issues
- None.

### Architectural Notes
- The troubleshooting updates correctly target runtime-process diagnosis rather than package-install assumptions.
- Guidance aligns with observed failure mode where older Provide a command to run with `uvx <command>`.

The following tools are installed:

- kimi-cli v1.9.0

See `uvx --help` for more information. environments continue serving active ports.

### Tests
- Quality gates executed during EXECUTE:
  - ============================= test session starts ==============================
platform darwin -- Python 3.10.19, pytest-9.0.2, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.10/bin/python3.10
cachedir: .pytest_cache
rootdir: /Users/egor/Development/GitHub/XcodeMCPWrapper
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 350 items

tests/integration/test_e2e.py::TestEndToEnd::test_full_cycle_with_mock_bridge SKIPPED [  0%]
tests/integration/test_e2e.py::TestEndToEnd::test_non_json_passthrough SKIPPED [  0%]
tests/integration/test_e2e.py::TestEndToEnd::test_already_compliant_response SKIPPED [  0%]
tests/integration/test_e2e.py::TestMockBridgeFixture::test_mock_bridge_outputs_expected_responses PASSED [  1%]
tests/integration/test_performance.py::TestPerformance::test_transformation_overhead_under_5ms PASSED [  1%]
tests/integration/test_performance.py::TestPerformance::test_large_json_processing_performance PASSED [  1%]
tests/integration/test_performance.py::TestPerformance::test_non_json_passthrough_performance PASSED [  2%]
tests/integration/test_performance.py::TestPerformance::test_memory_efficiency PASSED [  2%]
tests/integration/test_performance.py::TestBenchmarkReport::test_generate_benchmark_report SKIPPED [  2%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_full_request_lifecycle PASSED [  2%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_multiple_tools_workflow PASSED [  3%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_error_handling PASSED [  3%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_timeseries_data_accumulation PASSED [  3%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_metrics_reset PASSED [  4%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_audit_export_with_filtering PASSED [  4%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_concurrent_requests_simulation PASSED [  4%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_full_workplan PASSED [  4%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_task_details PASSED [  5%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_empty_workplan PASSED [  5%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_minimal_workplan PASSED [  5%]
tests/test_calc_progress.py::TestCalculateProgress::test_empty_tasks PASSED [  6%]
tests/test_calc_progress.py::TestCalculateProgress::test_single_task PASSED [  6%]
tests/test_calc_progress.py::TestCalculateProgress::test_multiple_priorities PASSED [  6%]
tests/test_calc_progress.py::TestCalculateProgress::test_completed_tasks PASSED [  6%]
tests/test_calc_progress.py::TestFormatProgress::test_text_format PASSED [  7%]
tests/test_calc_progress.py::TestFormatProgress::test_markdown_format PASSED [  7%]
tests/test_calc_progress.py::TestListTasks::test_list_all_tasks PASSED   [  7%]
tests/test_calc_progress.py::TestListTasks::test_list_by_phase PASSED    [  8%]
tests/test_calc_progress.py::TestListTasks::test_list_pending_only PASSED [  8%]
tests/test_calc_progress.py::TestCleanValue::test_removes_bold PASSED    [  8%]
tests/test_calc_progress.py::TestCleanValue::test_strips_whitespace PASSED [  8%]
tests/test_calc_progress.py::TestIntegration::test_script_runs_without_errors SKIPPED [  9%]
tests/test_calc_progress.py::TestIntegration::test_script_with_test_fixture PASSED [  9%]
tests/test_check_doc_sync.py::test_check_doc_sync_detects_unsynced_docs PASSED [  9%]
tests/test_check_doc_sync.py::test_check_doc_sync_accepts_synced_docs PASSED [ 10%]
tests/test_check_doc_sync.py::test_get_changed_files_branch_falls_back_when_origin_main_missing PASSED [ 10%]
tests/test_check_doc_sync.py::test_main_all_mode_checks_all_scopes_and_fails_on_unsynced PASSED [ 10%]
tests/test_check_doc_sync.py::test_main_all_mode_passes_when_all_scopes_synced PASSED [ 10%]
tests/unit/test_bridge.py::TestCreateBridge::test_create_bridge_basic PASSED [ 11%]
tests/unit/test_bridge.py::TestCreateBridge::test_create_bridge_with_args PASSED [ 11%]
tests/unit/test_bridge.py::TestCreateBridge::test_create_bridge_returns_popen_with_pipes PASSED [ 11%]
tests/unit/test_bridge.py::TestForwardStdin::test_forward_stdin_writes_line PASSED [ 12%]
tests/unit/test_bridge.py::TestForwardStdin::test_forward_stdin_handles_none_stdin PASSED [ 12%]
tests/unit/test_bridge.py::TestReadStdoutLine::test_read_stdout_line_returns_line PASSED [ 12%]
tests/unit/test_bridge.py::TestReadStdoutLine::test_read_stdout_line_returns_none_on_eof PASSED [ 12%]
tests/unit/test_bridge.py::TestCleanupBridge::test_cleanup_bridge_closes_stdin_and_waits PASSED [ 13%]
tests/unit/test_bridge.py::TestCleanupBridge::test_cleanup_bridge_handles_none_stdin PASSED [ 13%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_thread_is_daemon PASSED [ 13%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_writes_lines_to_bridge PASSED [ 14%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_flushes_after_each_write PASSED [ 14%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_handles_broken_pipe PASSED [ 14%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_handles_oserror PASSED [ 14%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_yields_complete_lines PASSED [ 15%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_handles_empty_stdout PASSED [ 15%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_stops_on_eof PASSED [ 15%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_passes_unmodified PASSED [ 16%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_is_generator PASSED [ 16%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_returns_thread_and_queue PASSED [ 16%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_puts_lines_in_queue PASSED [ 16%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_puts_none_sentinel_on_eof PASSED [ 17%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_handles_none_stdout PASSED [ 17%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_handles_broken_pipe PASSED [ 17%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_is_daemon_thread PASSED [ 18%]
tests/unit/test_bridge.py::TestStderrPassthrough::test_create_bridge_passes_stderr_to_popen PASSED [ 18%]
tests/unit/test_bridge.py::TestStderrPassthrough::test_create_bridge_stderr_not_captured PASSED [ 18%]
tests/unit/test_bridge.py::TestVerifyBridgeStarted::test_verify_returns_true_when_running PASSED [ 18%]
tests/unit/test_bridge.py::TestVerifyBridgeStarted::test_verify_returns_false_when_terminated PASSED [ 19%]
tests/unit/test_bridge.py::TestVerifyBridgeStarted::test_verify_returns_false_on_error PASSED [ 19%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_closes_stdin_and_waits_extra PASSED [ 19%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_handles_none_stdin PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_with_timeout PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_terminates_on_timeout_expired PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_kills_on_force_terminate_timeout PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_handles_broken_pipe_on_stdin_close PASSED [ 21%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_forwards_single_argument PASSED [ 21%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_forwards_multiple_arguments PASSED [ 21%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_handles_empty_args PASSED [ 22%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_handles_none_args PASSED [ 22%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_forwards_args_unmodified PASSED [ 22%]
tests/unit/test_cli.py::TestCliMain::test_cli_main_calls_main PASSED     [ 22%]
tests/unit/test_cli.py::TestCliMain::test_cli_main_returns_exit_code PASSED [ 23%]
tests/unit/test_main.py::TestMain::test_main_creates_bridge_and_threads PASSED [ 23%]
tests/unit/test_main.py::TestMain::test_main_processes_and_forwards_lines PASSED [ 23%]
tests/unit/test_main.py::TestMain::test_main_handles_keyboard_interrupt PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_returns_bridge_exit_code PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_passes_arguments_to_bridge PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_processes_response_line PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_passthrough_non_json PASSED [ 25%]
tests/unit/test_main.py::TestMain::test_main_writes_missing_newline PASSED [ 25%]
tests/unit/test_main.py::TestMain::test_main_diagnostic_printed_when_tools_list_no_response PASSED [ 25%]
tests/unit/test_main.py::TestMain::test_main_diagnostic_not_printed_when_exit_code_nonzero PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_handles_bridge_start_failure PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_records_metrics_for_tracked_request_and_response PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_does_not_record_metrics_when_request_has_no_method PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_sets_up_signal_handlers PASSED [ 27%]
tests/unit/test_main.py::TestMain::test_main_tracks_initialize_method PASSED [ 27%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_no_webui_args PASSED [ 27%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_flag PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_equals PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_config PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_config_equals PASSED [ 29%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_bridge_args_preserved PASSED [ 29%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_all_flags_together PASSED [ 29%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_non_numeric_raises PASSED [ 30%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_below_range_raises PASSED [ 30%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_above_range_raises PASSED [ 30%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_params_name PASSED [ 30%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_params_name_nested PASSED [ 31%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_method PASSED [ 31%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_result_name PASSED [ 31%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_result_toolname PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_skip_initialize_in_params PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_skip_tools_list_in_params PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_no_tool_found PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_invalid_json PASSED [ 33%]
tests/unit/test_main_webui.py::TestExtractToolName::test_non_dict_json PASSED [ 33%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_extract_id PASSED [ 33%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_extract_string_id PASSED [ 34%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_no_id PASSED   [ 34%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_invalid_json PASSED [ 34%]
tests/unit/test_main_webui.py::TestHasError::test_has_error_field PASSED [ 34%]
tests/unit/test_main_webui.py::TestHasError::test_no_error PASSED        [ 35%]
tests/unit/test_main_webui.py::TestHasError::test_invalid_json PASSED    [ 35%]
tests/unit/test_main_webui.py::TestHasError::test_non_dict_json PASSED   [ 35%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_webui_missing_deps PASSED [ 36%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_webui_enabled PASSED [ 36%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_webui_custom_port PASSED [ 36%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_invalid_webui_port PASSED [ 36%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_parses_all_tasks PASSED [ 37%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_task_details PASSED [ 37%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_trims_phase_title_suffix PASSED [ 37%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_dependencies PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_handles_no_dependencies PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_priorities PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_empty_workplan PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_nonexistent_file PASSED [ 39%]
tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p0 PASSED [ 39%]
tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p1 PASSED [ 39%]
tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p2 PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestTask::test_phase_number_extraction PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestTask::test_phase_number_two_digits PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_get_completed_empty_file PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_get_completed_with_data PASSED [ 41%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_save_completed_creates_file PASSED [ 41%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_save_completed_overwrites PASSED [ 41%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_round_trip PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_returns_highest_priority PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_respects_dependencies PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_returns_none_when_all_done PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_returns_none_for_empty_tasks PASSED [ 43%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_early_phase_priority PASSED [ 43%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_dependency_chain PASSED [ 43%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_includes_task_id PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_includes_description PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_shows_blocking_dependencies PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_shows_completed_dependencies PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_shows_progress PASSED [ 45%]
tests/unit/test_pick_next_task.py::TestMain::test_help_flag PASSED       [ 45%]
tests/unit/test_pick_next_task.py::TestMain::test_list_flag PASSED       [ 45%]
tests/unit/test_pick_next_task.py::TestMain::test_progress_flag PASSED   [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_done_flag PASSED       [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_done_invalid_task PASSED [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_default_shows_next_task PASSED [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_all_tasks_completed PASSED [ 47%]
tests/unit/test_pick_next_task.py::TestMain::test_missing_workplan PASSED [ 47%]
tests/unit/test_pick_next_task.py::TestIntegration::test_full_workflow PASSED [ 47%]
tests/unit/test_pick_next_task.py::TestIntegration::test_phase_filter PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[0.1.0] PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[1.2.3] PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[2.0.1-rc.1] PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[3.4.5+build.7] PASSED [ 49%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[1.2.3-rc.1+build.5] PASSED [ 49%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[1] PASSED [ 49%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[1.2] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[v1.2.3] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[01.2.3] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[1.2.3.4] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[] PASSED [ 51%]
tests/unit/test_publish_helper.py::TestPyprojectVersionUpdate::test_replace_project_version PASSED [ 51%]
tests/unit/test_publish_helper.py::TestPyprojectVersionUpdate::test_replace_project_version_missing_field_raises PASSED [ 51%]
tests/unit/test_publish_helper.py::TestUpdateFiles::test_updates_pyproject_and_server_json PASSED [ 52%]
tests/unit/test_publish_helper.py::TestUpdateFiles::test_dry_run_does_not_modify_files PASSED [ 52%]
tests/unit/test_publish_helper.py::test_main_rejects_invalid_version PASSED [ 52%]
tests/unit/test_publish_helper.py::test_main_dry_run_prints_next_commands PASSED [ 52%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_object PASSED [ 53%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_array PASSED [ 53%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_string_primitive PASSED [ 53%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_number_primitive PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_boolean_true PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_boolean_false PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_null PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_plain_text_rejection PASSED [ 55%]
tests/unit/test_transform.py::TestIsJsonLine::test_plain_text_with_colon PASSED [ 55%]
tests/unit/test_transform.py::TestIsJsonLine::test_partial_json_rejection PASSED [ 55%]
tests/unit/test_transform.py::TestIsJsonLine::test_empty_string PASSED   [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_whitespace_only PASSED [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_nested_json_object PASSED [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_json_with_special_characters PASSED [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_json_array_of_objects PASSED [ 57%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_object_returns_success PASSED [ 57%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_array_returns_success PASSED [ 57%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_string_primitive PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_number_primitive PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_boolean PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_null PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_invalid_json_returns_failure_with_original PASSED [ 59%]
tests/unit/test_transform.py::TestParseJsonSafe::test_partial_json_returns_failure PASSED [ 59%]
tests/unit/test_transform.py::TestParseJsonSafe::test_empty_string_returns_failure PASSED [ 59%]
tests/unit/test_transform.py::TestParseJsonSafe::test_whitespace_only_returns_failure PASSED [ 60%]
tests/unit/test_transform.py::TestParseJsonSafe::test_nested_json_object PASSED [ 60%]
tests/unit/test_transform.py::TestParseJsonSafe::test_complex_json_structure PASSED [ 60%]
tests/unit/test_transform.py::TestNeedsTransformation::test_content_without_structuredcontent_needs_transform PASSED [ 60%]
tests/unit/test_transform.py::TestNeedsTransformation::test_with_structuredcontent_no_transform_needed PASSED [ 61%]
tests/unit/test_transform.py::TestNeedsTransformation::test_without_result_field PASSED [ 61%]
tests/unit/test_transform.py::TestNeedsTransformation::test_with_empty_content_array PASSED [ 61%]
tests/unit/test_transform.py::TestNeedsTransformation::test_with_content_items PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_null_result PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_non_dict_result PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_non_dict_data PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_result_without_content PASSED [ 63%]
tests/unit/test_transform.py::TestNeedsTransformation::test_both_content_and_structuredcontent PASSED [ 63%]
tests/unit/test_transform.py::TestExtractTextContent::test_mixed_content_extracts_first_text PASSED [ 63%]
tests/unit/test_transform.py::TestExtractTextContent::test_single_text_item PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_multiple_text_items_returns_first PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_no_text_items_returns_none PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_empty_content_array PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_text_item_without_text_field PASSED [ 65%]
tests/unit/test_transform.py::TestExtractTextContent::test_non_dict_items_skipped PASSED [ 65%]
tests/unit/test_transform.py::TestExtractTextContent::test_text_field_not_string PASSED [ 65%]
tests/unit/test_transform.py::TestExtractTextContent::test_text_field_none PASSED [ 66%]
tests/unit/test_transform.py::TestExtractTextContent::test_complex_mcp_response_content PASSED [ 66%]
tests/unit/test_transform.py::TestParseStructuredContent::test_valid_json_object_string PASSED [ 66%]
tests/unit/test_transform.py::TestParseStructuredContent::test_valid_json_array_string PASSED [ 66%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_string_primitive PASSED [ 67%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_number_primitive PASSED [ 67%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_boolean_true PASSED [ 67%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_boolean_false PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_null PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_invalid_json_raises_exception PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_partial_json_raises_exception PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_empty_string_raises_exception PASSED [ 69%]
tests/unit/test_transform.py::TestParseStructuredContent::test_nested_json_object PASSED [ 69%]
tests/unit/test_transform.py::TestParseStructuredContent::test_complex_mcp_response_payload PASSED [ 69%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_valid_json_object_returns_parsed PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_valid_json_array_returns_parsed PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_json_string_primitive_returns_string PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_non_json_text_gets_wrapped PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_empty_string_gets_wrapped PASSED [ 71%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_partial_json_gets_wrapped PASSED [ 71%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_plain_text_with_special_chars_gets_wrapped PASSED [ 71%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_multiline_text_gets_wrapped PASSED [ 72%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_json_null_returns_none PASSED [ 72%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_json_boolean_returns_bool PASSED [ 72%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_injects_structuredcontent_for_valid_json PASSED [ 72%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_injects_structuredcontent_for_non_json PASSED [ 73%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_preserves_content_array PASSED [ 73%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_mutation_in_place PASSED [ 73%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_no_result_key PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_result_not_dict PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_no_content_key PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_content_not_list PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_no_text_items PASSED [ 75%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_empty_content_array PASSED [ 75%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_complex_json_payload PASSED [ 75%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_json_array_payload PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_json_line_with_trailing_newline_gets_transformed PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_plain_text_passthrough PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_non_json_error_message PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_json_needing_transformation PASSED [ 77%]
tests/unit/test_transform.py::TestProcessResponseLine::test_already_compliant_json PASSED [ 77%]
tests/unit/test_transform.py::TestProcessResponseLine::test_non_result_json PASSED [ 77%]
tests/unit/test_transform.py::TestProcessResponseLine::test_empty_line PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_whitespace_only PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_partial_json PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_json_with_non_json_text_content PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_preserves_other_json_fields PASSED [ 79%]
tests/unit/test_transform.py::TestProcessResponseLine::test_image_only_content_no_transformation PASSED [ 79%]
tests/unit/test_transform.py::TestProcessResponseLine::test_multiple_images_no_transformation PASSED [ 79%]
tests/unit/test_transform.py::TestProcessResponseLine::test_non_text_types_no_transformation PASSED [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_initial_state PASSED [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_entry PASSED   [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_with_error PASSED [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_with_request_response_data PASSED [ 81%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_disabled PASSED [ 81%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_get_entries_pagination PASSED [ 81%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_get_entries_tool_filter PASSED [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_json PASSED [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_json_with_limit PASSED [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_csv PASSED  [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_csv_empty PASSED [ 83%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_file_rotation PASSED [ 83%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_cleanup_old_files PASSED [ 83%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_thread_safety PASSED [ 84%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_close_idempotent PASSED [ 84%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_default_values PASSED [ 84%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_config_from_file PASSED [ 84%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_config_merge_nested PASSED [ 85%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_host PASSED [ 85%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_port PASSED [ 85%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_auth_enabled PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_auth_credentials PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_to_dict_masks_password PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_invalid_config_file_ignored PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_merge_does_not_affect_original_defaults PASSED [ 87%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_initial_state PASSED [ 87%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_request PASSED [ 87%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_multiple_requests_same_tool PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_requests_different_tools PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_request_with_request_id PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_response_with_latency PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_response_computes_latency_from_request PASSED [ 89%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_error_response PASSED [ 89%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_error_convenience_method PASSED [ 89%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_rps_calculation PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_error_rate_calculation PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_latency_percentiles PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_get_timeseries PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_reset PASSED [ 91%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_thread_safety PASSED [ 91%]
tests/unit/webui/test_server.py::TestCreateApp::test_health_endpoint PASSED [ 91%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_metrics PASSED  [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_timeseries PASSED [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_reset_metrics PASSED [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_audit_logs PASSED [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_audit_logs_with_pagination PASSED [ 93%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_audit_logs_with_filter PASSED [ 93%]
tests/unit/webui/test_server.py::TestCreateApp::test_export_audit_json PASSED [ 93%]
tests/unit/webui/test_server.py::TestCreateApp::test_export_audit_csv PASSED [ 94%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_config PASSED   [ 94%]
tests/unit/webui/test_server.py::TestCreateApp::test_dashboard_served PASSED [ 94%]
tests/unit/webui/test_server.py::TestAuth::test_auth_required PASSED     [ 94%]
tests/unit/webui/test_server.py::TestAuth::test_auth_with_valid_credentials PASSED [ 95%]
tests/unit/webui/test_server.py::TestAuth::test_auth_with_invalid_credentials PASSED [ 95%]
tests/unit/webui/test_server.py::TestAuth::test_health_no_auth_required PASSED [ 95%]
tests/unit/webui/test_server.py::TestAuth::test_dashboard_injects_ws_token PASSED [ 96%]
tests/unit/webui/test_server.py::TestAuth::test_websocket_auth_with_query_token PASSED [ 96%]
tests/unit/webui/test_server.py::TestAuth::test_websocket_auth_with_basic_header PASSED [ 96%]
tests/unit/webui/test_server.py::TestAuth::test_websocket_auth_rejects_missing_credentials PASSED [ 96%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_record_request PASSED [ 97%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_record_response PASSED [ 97%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_record_error PASSED [ 97%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_format PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_point_format PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_t_values_are_seconds_ago PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_buckets_requests PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_error_counting PASSED [ 99%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_uptime_is_dynamic PASSED [ 99%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_uptime_independent_of_window_seconds PASSED [ 99%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_reset_clears_all_data PASSED [100%]

=============================== warnings summary ===============================
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_dependencies
  /opt/homebrew/lib/python3.10/site-packages/websockets/legacy/__init__.py:6: DeprecationWarning: websockets.legacy is deprecated; see https://websockets.readthedocs.io/en/stable/howto/upgrade.html for upgrade instructions
    warnings.warn(  # deprecated in 14.0 - 2024-11-09

tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_priorities
  /opt/homebrew/lib/python3.10/site-packages/uvicorn/protocols/websockets/websockets_impl.py:17: DeprecationWarning: websockets.server.WebSocketServerProtocol is deprecated
    from websockets.server import WebSocketServerProtocol

tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p1
  /opt/homebrew/lib/python3.10/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread webui-server
  
  Traceback (most recent call last):
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 164, in startup
      server = await loop.create_server(
    File "uvloop/loop.pyx", line 1794, in create_server
  OSError: [Errno 48] error while attempting to bind on address ('127.0.0.1', 8080): address already in use
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/opt/homebrew/Cellar/python@3.10/3.10.19_2/Frameworks/Python.framework/Versions/3.10/lib/python3.10/threading.py", line 1016, in _bootstrap_inner
      self.run()
    File "/opt/homebrew/Cellar/python@3.10/3.10.19_2/Frameworks/Python.framework/Versions/3.10/lib/python3.10/threading.py", line 953, in run
      self._target(*self._args, **self._kwargs)
    File "/Users/egor/Development/GitHub/XcodeMCPWrapper/src/mcpbridge_wrapper/webui/server.py", line 343, in run_server
      uvicorn.run(
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/main.py", line 593, in run
      server.run()
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 67, in run
      return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/_compat.py", line 60, in asyncio_run
      return loop.run_until_complete(main)
    File "uvloop/loop.pyx", line 1512, in uvloop.loop.Loop.run_until_complete
    File "uvloop/loop.pyx", line 1505, in uvloop.loop.Loop.run_until_complete
    File "uvloop/loop.pyx", line 1379, in uvloop.loop.Loop.run_forever
    File "uvloop/loop.pyx", line 557, in uvloop.loop.Loop._run
    File "uvloop/loop.pyx", line 476, in uvloop.loop.Loop._on_idle
    File "uvloop/cbhandles.pyx", line 83, in uvloop.loop.Handle._run
    File "uvloop/cbhandles.pyx", line 63, in uvloop.loop.Handle._run
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 71, in serve
      await self._serve(sockets)
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 86, in _serve
      await self.startup(sockets=sockets)
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 174, in startup
      sys.exit(1)
  SystemExit: 1
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================== 345 passed, 5 skipped, 3 warnings in 0.74s ================== (pass)
  - All checks passed! (pass)
  - Success: no issues found in 12 source files (pass)
  - ============================= test session starts ==============================
platform darwin -- Python 3.10.19, pytest-9.0.2, pluggy-1.6.0 -- /opt/homebrew/opt/python@3.10/bin/python3.10
cachedir: .pytest_cache
rootdir: /Users/egor/Development/GitHub/XcodeMCPWrapper
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.12.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=strict, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collecting ... collected 350 items

tests/integration/test_e2e.py::TestEndToEnd::test_full_cycle_with_mock_bridge SKIPPED [  0%]
tests/integration/test_e2e.py::TestEndToEnd::test_non_json_passthrough SKIPPED [  0%]
tests/integration/test_e2e.py::TestEndToEnd::test_already_compliant_response SKIPPED [  0%]
tests/integration/test_e2e.py::TestMockBridgeFixture::test_mock_bridge_outputs_expected_responses PASSED [  1%]
tests/integration/test_performance.py::TestPerformance::test_transformation_overhead_under_5ms PASSED [  1%]
tests/integration/test_performance.py::TestPerformance::test_large_json_processing_performance PASSED [  1%]
tests/integration/test_performance.py::TestPerformance::test_non_json_passthrough_performance PASSED [  2%]
tests/integration/test_performance.py::TestPerformance::test_memory_efficiency PASSED [  2%]
tests/integration/test_performance.py::TestBenchmarkReport::test_generate_benchmark_report SKIPPED [  2%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_full_request_lifecycle PASSED [  2%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_multiple_tools_workflow PASSED [  3%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_error_handling PASSED [  3%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_timeseries_data_accumulation PASSED [  3%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_metrics_reset PASSED [  4%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_audit_export_with_filtering PASSED [  4%]
tests/integration/webui/test_e2e.py::TestEndToEnd::test_concurrent_requests_simulation PASSED [  4%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_full_workplan PASSED [  4%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_task_details PASSED [  5%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_empty_workplan PASSED [  5%]
tests/test_calc_progress.py::TestParseWorkplan::test_parse_minimal_workplan PASSED [  5%]
tests/test_calc_progress.py::TestCalculateProgress::test_empty_tasks PASSED [  6%]
tests/test_calc_progress.py::TestCalculateProgress::test_single_task PASSED [  6%]
tests/test_calc_progress.py::TestCalculateProgress::test_multiple_priorities PASSED [  6%]
tests/test_calc_progress.py::TestCalculateProgress::test_completed_tasks PASSED [  6%]
tests/test_calc_progress.py::TestFormatProgress::test_text_format PASSED [  7%]
tests/test_calc_progress.py::TestFormatProgress::test_markdown_format PASSED [  7%]
tests/test_calc_progress.py::TestListTasks::test_list_all_tasks PASSED   [  7%]
tests/test_calc_progress.py::TestListTasks::test_list_by_phase PASSED    [  8%]
tests/test_calc_progress.py::TestListTasks::test_list_pending_only PASSED [  8%]
tests/test_calc_progress.py::TestCleanValue::test_removes_bold PASSED    [  8%]
tests/test_calc_progress.py::TestCleanValue::test_strips_whitespace PASSED [  8%]
tests/test_calc_progress.py::TestIntegration::test_script_runs_without_errors SKIPPED [  9%]
tests/test_calc_progress.py::TestIntegration::test_script_with_test_fixture PASSED [  9%]
tests/test_check_doc_sync.py::test_check_doc_sync_detects_unsynced_docs PASSED [  9%]
tests/test_check_doc_sync.py::test_check_doc_sync_accepts_synced_docs PASSED [ 10%]
tests/test_check_doc_sync.py::test_get_changed_files_branch_falls_back_when_origin_main_missing PASSED [ 10%]
tests/test_check_doc_sync.py::test_main_all_mode_checks_all_scopes_and_fails_on_unsynced PASSED [ 10%]
tests/test_check_doc_sync.py::test_main_all_mode_passes_when_all_scopes_synced PASSED [ 10%]
tests/unit/test_bridge.py::TestCreateBridge::test_create_bridge_basic PASSED [ 11%]
tests/unit/test_bridge.py::TestCreateBridge::test_create_bridge_with_args PASSED [ 11%]
tests/unit/test_bridge.py::TestCreateBridge::test_create_bridge_returns_popen_with_pipes PASSED [ 11%]
tests/unit/test_bridge.py::TestForwardStdin::test_forward_stdin_writes_line PASSED [ 12%]
tests/unit/test_bridge.py::TestForwardStdin::test_forward_stdin_handles_none_stdin PASSED [ 12%]
tests/unit/test_bridge.py::TestReadStdoutLine::test_read_stdout_line_returns_line PASSED [ 12%]
tests/unit/test_bridge.py::TestReadStdoutLine::test_read_stdout_line_returns_none_on_eof PASSED [ 12%]
tests/unit/test_bridge.py::TestCleanupBridge::test_cleanup_bridge_closes_stdin_and_waits PASSED [ 13%]
tests/unit/test_bridge.py::TestCleanupBridge::test_cleanup_bridge_handles_none_stdin PASSED [ 13%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_thread_is_daemon PASSED [ 13%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_writes_lines_to_bridge PASSED [ 14%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_flushes_after_each_write PASSED [ 14%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_handles_broken_pipe PASSED [ 14%]
tests/unit/test_bridge.py::TestRunStdinForwarder::test_forwarder_handles_oserror PASSED [ 14%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_yields_complete_lines PASSED [ 15%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_handles_empty_stdout PASSED [ 15%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_stops_on_eof PASSED [ 15%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_passes_unmodified PASSED [ 16%]
tests/unit/test_bridge.py::TestReadStdout::test_read_stdout_is_generator PASSED [ 16%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_returns_thread_and_queue PASSED [ 16%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_puts_lines_in_queue PASSED [ 16%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_puts_none_sentinel_on_eof PASSED [ 17%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_handles_none_stdout PASSED [ 17%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_handles_broken_pipe PASSED [ 17%]
tests/unit/test_bridge.py::TestRunStdoutReader::test_reader_is_daemon_thread PASSED [ 18%]
tests/unit/test_bridge.py::TestStderrPassthrough::test_create_bridge_passes_stderr_to_popen PASSED [ 18%]
tests/unit/test_bridge.py::TestStderrPassthrough::test_create_bridge_stderr_not_captured PASSED [ 18%]
tests/unit/test_bridge.py::TestVerifyBridgeStarted::test_verify_returns_true_when_running PASSED [ 18%]
tests/unit/test_bridge.py::TestVerifyBridgeStarted::test_verify_returns_false_when_terminated PASSED [ 19%]
tests/unit/test_bridge.py::TestVerifyBridgeStarted::test_verify_returns_false_on_error PASSED [ 19%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_closes_stdin_and_waits_extra PASSED [ 19%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_handles_none_stdin PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_with_timeout PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_terminates_on_timeout_expired PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_kills_on_force_terminate_timeout PASSED [ 20%]
tests/unit/test_bridge.py::TestCleanupBridgeExtra::test_cleanup_handles_broken_pipe_on_stdin_close PASSED [ 21%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_forwards_single_argument PASSED [ 21%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_forwards_multiple_arguments PASSED [ 21%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_handles_empty_args PASSED [ 22%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_handles_none_args PASSED [ 22%]
tests/unit/test_bridge.py::TestForwardCommandLineArguments::test_create_bridge_forwards_args_unmodified PASSED [ 22%]
tests/unit/test_cli.py::TestCliMain::test_cli_main_calls_main PASSED     [ 22%]
tests/unit/test_cli.py::TestCliMain::test_cli_main_returns_exit_code PASSED [ 23%]
tests/unit/test_main.py::TestMain::test_main_creates_bridge_and_threads PASSED [ 23%]
tests/unit/test_main.py::TestMain::test_main_processes_and_forwards_lines PASSED [ 23%]
tests/unit/test_main.py::TestMain::test_main_handles_keyboard_interrupt PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_returns_bridge_exit_code PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_passes_arguments_to_bridge PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_processes_response_line PASSED [ 24%]
tests/unit/test_main.py::TestMain::test_main_passthrough_non_json PASSED [ 25%]
tests/unit/test_main.py::TestMain::test_main_writes_missing_newline PASSED [ 25%]
tests/unit/test_main.py::TestMain::test_main_diagnostic_printed_when_tools_list_no_response PASSED [ 25%]
tests/unit/test_main.py::TestMain::test_main_diagnostic_not_printed_when_exit_code_nonzero PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_handles_bridge_start_failure PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_records_metrics_for_tracked_request_and_response PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_does_not_record_metrics_when_request_has_no_method PASSED [ 26%]
tests/unit/test_main.py::TestMain::test_main_sets_up_signal_handlers PASSED [ 27%]
tests/unit/test_main.py::TestMain::test_main_tracks_initialize_method PASSED [ 27%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_no_webui_args PASSED [ 27%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_flag PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_equals PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_config PASSED [ 28%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_config_equals PASSED [ 29%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_bridge_args_preserved PASSED [ 29%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_all_flags_together PASSED [ 29%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_non_numeric_raises PASSED [ 30%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_below_range_raises PASSED [ 30%]
tests/unit/test_main_webui.py::TestParseWebUIArgs::test_webui_port_above_range_raises PASSED [ 30%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_params_name PASSED [ 30%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_params_name_nested PASSED [ 31%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_method PASSED [ 31%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_result_name PASSED [ 31%]
tests/unit/test_main_webui.py::TestExtractToolName::test_extract_from_result_toolname PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_skip_initialize_in_params PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_skip_tools_list_in_params PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_no_tool_found PASSED [ 32%]
tests/unit/test_main_webui.py::TestExtractToolName::test_invalid_json PASSED [ 33%]
tests/unit/test_main_webui.py::TestExtractToolName::test_non_dict_json PASSED [ 33%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_extract_id PASSED [ 33%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_extract_string_id PASSED [ 34%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_no_id PASSED   [ 34%]
tests/unit/test_main_webui.py::TestExtractRequestId::test_invalid_json PASSED [ 34%]
tests/unit/test_main_webui.py::TestHasError::test_has_error_field PASSED [ 34%]
tests/unit/test_main_webui.py::TestHasError::test_no_error PASSED        [ 35%]
tests/unit/test_main_webui.py::TestHasError::test_invalid_json PASSED    [ 35%]
tests/unit/test_main_webui.py::TestHasError::test_non_dict_json PASSED   [ 35%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_webui_missing_deps PASSED [ 36%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_webui_enabled PASSED [ 36%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_webui_custom_port PASSED [ 36%]
tests/unit/test_main_webui.py::TestMainWebUI::test_main_with_invalid_webui_port PASSED [ 36%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_parses_all_tasks PASSED [ 37%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_task_details PASSED [ 37%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_trims_phase_title_suffix PASSED [ 37%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_dependencies PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_handles_no_dependencies PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_extracts_priorities PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_empty_workplan PASSED [ 38%]
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_nonexistent_file PASSED [ 39%]
tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p0 PASSED [ 39%]
tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p1 PASSED [ 39%]
tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p2 PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestTask::test_phase_number_extraction PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestTask::test_phase_number_two_digits PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_get_completed_empty_file PASSED [ 40%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_get_completed_with_data PASSED [ 41%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_save_completed_creates_file PASSED [ 41%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_save_completed_overwrites PASSED [ 41%]
tests/unit/test_pick_next_task.py::TestCompletedTasks::test_round_trip PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_returns_highest_priority PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_respects_dependencies PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_returns_none_when_all_done PASSED [ 42%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_returns_none_for_empty_tasks PASSED [ 43%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_early_phase_priority PASSED [ 43%]
tests/unit/test_pick_next_task.py::TestFindNextTask::test_dependency_chain PASSED [ 43%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_includes_task_id PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_includes_description PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_shows_blocking_dependencies PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_shows_completed_dependencies PASSED [ 44%]
tests/unit/test_pick_next_task.py::TestFormatTaskOutput::test_shows_progress PASSED [ 45%]
tests/unit/test_pick_next_task.py::TestMain::test_help_flag PASSED       [ 45%]
tests/unit/test_pick_next_task.py::TestMain::test_list_flag PASSED       [ 45%]
tests/unit/test_pick_next_task.py::TestMain::test_progress_flag PASSED   [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_done_flag PASSED       [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_done_invalid_task PASSED [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_default_shows_next_task PASSED [ 46%]
tests/unit/test_pick_next_task.py::TestMain::test_all_tasks_completed PASSED [ 47%]
tests/unit/test_pick_next_task.py::TestMain::test_missing_workplan PASSED [ 47%]
tests/unit/test_pick_next_task.py::TestIntegration::test_full_workflow PASSED [ 47%]
tests/unit/test_pick_next_task.py::TestIntegration::test_phase_filter PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[0.1.0] PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[1.2.3] PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[2.0.1-rc.1] PASSED [ 48%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[3.4.5+build.7] PASSED [ 49%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_accepts_valid_semver[1.2.3-rc.1+build.5] PASSED [ 49%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[1] PASSED [ 49%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[1.2] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[v1.2.3] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[01.2.3] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[1.2.3.4] PASSED [ 50%]
tests/unit/test_publish_helper.py::TestValidateSemver::test_rejects_invalid_semver[] PASSED [ 51%]
tests/unit/test_publish_helper.py::TestPyprojectVersionUpdate::test_replace_project_version PASSED [ 51%]
tests/unit/test_publish_helper.py::TestPyprojectVersionUpdate::test_replace_project_version_missing_field_raises PASSED [ 51%]
tests/unit/test_publish_helper.py::TestUpdateFiles::test_updates_pyproject_and_server_json PASSED [ 52%]
tests/unit/test_publish_helper.py::TestUpdateFiles::test_dry_run_does_not_modify_files PASSED [ 52%]
tests/unit/test_publish_helper.py::test_main_rejects_invalid_version PASSED [ 52%]
tests/unit/test_publish_helper.py::test_main_dry_run_prints_next_commands PASSED [ 52%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_object PASSED [ 53%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_array PASSED [ 53%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_string_primitive PASSED [ 53%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_number_primitive PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_boolean_true PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_boolean_false PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_valid_json_null PASSED [ 54%]
tests/unit/test_transform.py::TestIsJsonLine::test_plain_text_rejection PASSED [ 55%]
tests/unit/test_transform.py::TestIsJsonLine::test_plain_text_with_colon PASSED [ 55%]
tests/unit/test_transform.py::TestIsJsonLine::test_partial_json_rejection PASSED [ 55%]
tests/unit/test_transform.py::TestIsJsonLine::test_empty_string PASSED   [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_whitespace_only PASSED [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_nested_json_object PASSED [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_json_with_special_characters PASSED [ 56%]
tests/unit/test_transform.py::TestIsJsonLine::test_json_array_of_objects PASSED [ 57%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_object_returns_success PASSED [ 57%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_array_returns_success PASSED [ 57%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_string_primitive PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_number_primitive PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_boolean PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_valid_json_null PASSED [ 58%]
tests/unit/test_transform.py::TestParseJsonSafe::test_invalid_json_returns_failure_with_original PASSED [ 59%]
tests/unit/test_transform.py::TestParseJsonSafe::test_partial_json_returns_failure PASSED [ 59%]
tests/unit/test_transform.py::TestParseJsonSafe::test_empty_string_returns_failure PASSED [ 59%]
tests/unit/test_transform.py::TestParseJsonSafe::test_whitespace_only_returns_failure PASSED [ 60%]
tests/unit/test_transform.py::TestParseJsonSafe::test_nested_json_object PASSED [ 60%]
tests/unit/test_transform.py::TestParseJsonSafe::test_complex_json_structure PASSED [ 60%]
tests/unit/test_transform.py::TestNeedsTransformation::test_content_without_structuredcontent_needs_transform PASSED [ 60%]
tests/unit/test_transform.py::TestNeedsTransformation::test_with_structuredcontent_no_transform_needed PASSED [ 61%]
tests/unit/test_transform.py::TestNeedsTransformation::test_without_result_field PASSED [ 61%]
tests/unit/test_transform.py::TestNeedsTransformation::test_with_empty_content_array PASSED [ 61%]
tests/unit/test_transform.py::TestNeedsTransformation::test_with_content_items PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_null_result PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_non_dict_result PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_non_dict_data PASSED [ 62%]
tests/unit/test_transform.py::TestNeedsTransformation::test_result_without_content PASSED [ 63%]
tests/unit/test_transform.py::TestNeedsTransformation::test_both_content_and_structuredcontent PASSED [ 63%]
tests/unit/test_transform.py::TestExtractTextContent::test_mixed_content_extracts_first_text PASSED [ 63%]
tests/unit/test_transform.py::TestExtractTextContent::test_single_text_item PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_multiple_text_items_returns_first PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_no_text_items_returns_none PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_empty_content_array PASSED [ 64%]
tests/unit/test_transform.py::TestExtractTextContent::test_text_item_without_text_field PASSED [ 65%]
tests/unit/test_transform.py::TestExtractTextContent::test_non_dict_items_skipped PASSED [ 65%]
tests/unit/test_transform.py::TestExtractTextContent::test_text_field_not_string PASSED [ 65%]
tests/unit/test_transform.py::TestExtractTextContent::test_text_field_none PASSED [ 66%]
tests/unit/test_transform.py::TestExtractTextContent::test_complex_mcp_response_content PASSED [ 66%]
tests/unit/test_transform.py::TestParseStructuredContent::test_valid_json_object_string PASSED [ 66%]
tests/unit/test_transform.py::TestParseStructuredContent::test_valid_json_array_string PASSED [ 66%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_string_primitive PASSED [ 67%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_number_primitive PASSED [ 67%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_boolean_true PASSED [ 67%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_boolean_false PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_json_null PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_invalid_json_raises_exception PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_partial_json_raises_exception PASSED [ 68%]
tests/unit/test_transform.py::TestParseStructuredContent::test_empty_string_raises_exception PASSED [ 69%]
tests/unit/test_transform.py::TestParseStructuredContent::test_nested_json_object PASSED [ 69%]
tests/unit/test_transform.py::TestParseStructuredContent::test_complex_mcp_response_payload PASSED [ 69%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_valid_json_object_returns_parsed PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_valid_json_array_returns_parsed PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_json_string_primitive_returns_string PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_non_json_text_gets_wrapped PASSED [ 70%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_empty_string_gets_wrapped PASSED [ 71%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_partial_json_gets_wrapped PASSED [ 71%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_plain_text_with_special_chars_gets_wrapped PASSED [ 71%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_multiline_text_gets_wrapped PASSED [ 72%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_json_null_returns_none PASSED [ 72%]
tests/unit/test_transform.py::TestParseStructuredContentWithFallback::test_json_boolean_returns_bool PASSED [ 72%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_injects_structuredcontent_for_valid_json PASSED [ 72%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_injects_structuredcontent_for_non_json PASSED [ 73%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_preserves_content_array PASSED [ 73%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_mutation_in_place PASSED [ 73%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_no_result_key PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_result_not_dict PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_no_content_key PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_content_not_list PASSED [ 74%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_no_text_items PASSED [ 75%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_empty_content_array PASSED [ 75%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_complex_json_payload PASSED [ 75%]
tests/unit/test_transform.py::TestInjectStructuredContent::test_json_array_payload PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_json_line_with_trailing_newline_gets_transformed PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_plain_text_passthrough PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_non_json_error_message PASSED [ 76%]
tests/unit/test_transform.py::TestProcessResponseLine::test_json_needing_transformation PASSED [ 77%]
tests/unit/test_transform.py::TestProcessResponseLine::test_already_compliant_json PASSED [ 77%]
tests/unit/test_transform.py::TestProcessResponseLine::test_non_result_json PASSED [ 77%]
tests/unit/test_transform.py::TestProcessResponseLine::test_empty_line PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_whitespace_only PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_partial_json PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_json_with_non_json_text_content PASSED [ 78%]
tests/unit/test_transform.py::TestProcessResponseLine::test_preserves_other_json_fields PASSED [ 79%]
tests/unit/test_transform.py::TestProcessResponseLine::test_image_only_content_no_transformation PASSED [ 79%]
tests/unit/test_transform.py::TestProcessResponseLine::test_multiple_images_no_transformation PASSED [ 79%]
tests/unit/test_transform.py::TestProcessResponseLine::test_non_text_types_no_transformation PASSED [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_initial_state PASSED [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_entry PASSED   [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_with_error PASSED [ 80%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_with_request_response_data PASSED [ 81%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_log_disabled PASSED [ 81%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_get_entries_pagination PASSED [ 81%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_get_entries_tool_filter PASSED [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_json PASSED [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_json_with_limit PASSED [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_csv PASSED  [ 82%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_export_csv_empty PASSED [ 83%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_file_rotation PASSED [ 83%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_cleanup_old_files PASSED [ 83%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_thread_safety PASSED [ 84%]
tests/unit/webui/test_audit.py::TestAuditLogger::test_close_idempotent PASSED [ 84%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_default_values PASSED [ 84%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_config_from_file PASSED [ 84%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_config_merge_nested PASSED [ 85%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_host PASSED [ 85%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_port PASSED [ 85%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_auth_enabled PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_env_override_auth_credentials PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_to_dict_masks_password PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_invalid_config_file_ignored PASSED [ 86%]
tests/unit/webui/test_config.py::TestWebUIConfig::test_merge_does_not_affect_original_defaults PASSED [ 87%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_initial_state PASSED [ 87%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_request PASSED [ 87%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_multiple_requests_same_tool PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_requests_different_tools PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_request_with_request_id PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_response_with_latency PASSED [ 88%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_response_computes_latency_from_request PASSED [ 89%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_error_response PASSED [ 89%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_record_error_convenience_method PASSED [ 89%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_rps_calculation PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_error_rate_calculation PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_latency_percentiles PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_get_timeseries PASSED [ 90%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_reset PASSED [ 91%]
tests/unit/webui/test_metrics.py::TestMetricsCollector::test_thread_safety PASSED [ 91%]
tests/unit/webui/test_server.py::TestCreateApp::test_health_endpoint PASSED [ 91%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_metrics PASSED  [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_timeseries PASSED [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_reset_metrics PASSED [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_audit_logs PASSED [ 92%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_audit_logs_with_pagination PASSED [ 93%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_audit_logs_with_filter PASSED [ 93%]
tests/unit/webui/test_server.py::TestCreateApp::test_export_audit_json PASSED [ 93%]
tests/unit/webui/test_server.py::TestCreateApp::test_export_audit_csv PASSED [ 94%]
tests/unit/webui/test_server.py::TestCreateApp::test_get_config PASSED   [ 94%]
tests/unit/webui/test_server.py::TestCreateApp::test_dashboard_served PASSED [ 94%]
tests/unit/webui/test_server.py::TestAuth::test_auth_required PASSED     [ 94%]
tests/unit/webui/test_server.py::TestAuth::test_auth_with_valid_credentials PASSED [ 95%]
tests/unit/webui/test_server.py::TestAuth::test_auth_with_invalid_credentials PASSED [ 95%]
tests/unit/webui/test_server.py::TestAuth::test_health_no_auth_required PASSED [ 95%]
tests/unit/webui/test_server.py::TestAuth::test_dashboard_injects_ws_token PASSED [ 96%]
tests/unit/webui/test_server.py::TestAuth::test_websocket_auth_with_query_token PASSED [ 96%]
tests/unit/webui/test_server.py::TestAuth::test_websocket_auth_with_basic_header PASSED [ 96%]
tests/unit/webui/test_server.py::TestAuth::test_websocket_auth_rejects_missing_credentials PASSED [ 96%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_record_request PASSED [ 97%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_record_response PASSED [ 97%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_record_error PASSED [ 97%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_format PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_point_format PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_t_values_are_seconds_ago PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_buckets_requests PASSED [ 98%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_get_timeseries_error_counting PASSED [ 99%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_uptime_is_dynamic PASSED [ 99%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_uptime_independent_of_window_seconds PASSED [ 99%]
tests/unit/webui/test_shared_metrics.py::TestSharedMetricsStore::test_reset_clears_all_data PASSED [100%]

=============================== warnings summary ===============================
tests/unit/test_pick_next_task.py::TestParseWorkplan::test_handles_no_dependencies
  /opt/homebrew/lib/python3.10/site-packages/websockets/legacy/__init__.py:6: DeprecationWarning: websockets.legacy is deprecated; see https://websockets.readthedocs.io/en/stable/howto/upgrade.html for upgrade instructions
    warnings.warn(  # deprecated in 14.0 - 2024-11-09

tests/unit/test_pick_next_task.py::TestTask::test_priority_value_p0
  /opt/homebrew/lib/python3.10/site-packages/uvicorn/protocols/websockets/websockets_impl.py:17: DeprecationWarning: websockets.server.WebSocketServerProtocol is deprecated
    from websockets.server import WebSocketServerProtocol

tests/unit/test_pick_next_task.py::TestCompletedTasks::test_get_completed_with_data
  /opt/homebrew/lib/python3.10/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread webui-server
  
  Traceback (most recent call last):
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 164, in startup
      server = await loop.create_server(
    File "uvloop/loop.pyx", line 1794, in create_server
  OSError: [Errno 48] error while attempting to bind on address ('127.0.0.1', 8080): address already in use
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/opt/homebrew/Cellar/python@3.10/3.10.19_2/Frameworks/Python.framework/Versions/3.10/lib/python3.10/threading.py", line 1016, in _bootstrap_inner
      self.run()
    File "/opt/homebrew/Cellar/python@3.10/3.10.19_2/Frameworks/Python.framework/Versions/3.10/lib/python3.10/threading.py", line 953, in run
      self._target(*self._args, **self._kwargs)
    File "/Users/egor/Development/GitHub/XcodeMCPWrapper/src/mcpbridge_wrapper/webui/server.py", line 343, in run_server
      uvicorn.run(
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/main.py", line 593, in run
      server.run()
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 67, in run
      return asyncio_run(self.serve(sockets=sockets), loop_factory=self.config.get_loop_factory())
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/_compat.py", line 60, in asyncio_run
      return loop.run_until_complete(main)
    File "uvloop/loop.pyx", line 1512, in uvloop.loop.Loop.run_until_complete
    File "uvloop/loop.pyx", line 1505, in uvloop.loop.Loop.run_until_complete
    File "uvloop/loop.pyx", line 1379, in uvloop.loop.Loop.run_forever
    File "uvloop/loop.pyx", line 557, in uvloop.loop.Loop._run
    File "uvloop/loop.pyx", line 476, in uvloop.loop.Loop._on_idle
    File "uvloop/cbhandles.pyx", line 83, in uvloop.loop.Handle._run
    File "uvloop/cbhandles.pyx", line 63, in uvloop.loop.Handle._run
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 71, in serve
      await self._serve(sockets)
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 86, in _serve
      await self.startup(sockets=sockets)
    File "/opt/homebrew/lib/python3.10/site-packages/uvicorn/server.py", line 174, in startup
      sys.exit(1)
  SystemExit: 1
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================================ tests coverage ================================
______________ coverage: platform darwin, python 3.10.19-final-0 _______________

Name                                 Stmts   Miss Branch BrPart  Cover
----------------------------------------------------------------------
src/mcpbridge_wrapper/__init__.py        4      0      0      0 100.0%
src/mcpbridge_wrapper/__main__.py      155      4     46      3  96.5%
src/mcpbridge_wrapper/bridge.py         71      2     22      2  95.7%
src/mcpbridge_wrapper/cli.py             4      0      0      0 100.0%
src/mcpbridge_wrapper/schemas.py        42      2      8      0  96.0%
src/mcpbridge_wrapper/transform.py      64      1     28      1  97.8%
----------------------------------------------------------------------
TOTAL                                  340      9    104      6  96.6%
Required test coverage of 90.0% reached. Total coverage: 96.62%
================== 345 passed, 5 skipped, 3 warnings in 1.11s ================== (pass, 96.62% >= 90%)
- No source-code behavior changes; docs-only updates validated with local stale-vs-refresh repro evidence.

### Next Steps
- FOLLOW-UP skipped: no actionable review findings.
