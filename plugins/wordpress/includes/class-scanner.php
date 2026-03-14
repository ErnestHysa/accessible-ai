<?php
/**
 * Scanner class for running accessibility scans
 */

class Accessible_AI_Scanner {

    private $api_client;

    public function __construct($api_client) {
        $this->api_client = $api_client;
    }

    /**
     * Run a scan via AJAX
     */
    public function run_scan() {
        check_ajax_referer('accessible_ai_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }

        $full_scan = isset($_POST['full_scan']) && $_POST['full_scan'] === 'true';

        $result = $this->api_client->trigger_scan($full_scan);

        if (is_wp_error($result)) {
            wp_send_json_error(array('message' => $result->get_error_message()));
        }

        // Store scan ID for later retrieval
        update_option('accessible_ai_current_scan_id', $result['scan_id']);

        wp_send_json_success(array(
            'scan_id' => $result['scan_id'],
            'status' => $result['status'],
            'message' => $result['message'],
        ));
    }

    /**
     * Get scan results via AJAX
     */
    public function get_scan_results() {
        check_ajax_referer('accessible_ai_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }

        $scan_id = isset($_POST['scan_id']) ? sanitize_text_field($_POST['scan_id']) : get_option('accessible_ai_current_scan_id');

        if (empty($scan_id)) {
            wp_send_json_error(array('message' => 'No scan ID provided'));
        }

        $result = $this->api_client->get_scan_results($scan_id);

        if (is_wp_error($result)) {
            wp_send_json_error(array('message' => $result->get_error_message()));
        }

        // Update latest score
        if (isset($result['score']) && $result['status'] === 'completed') {
            update_option('accessible_ai_latest_score', $result['score']);
            update_option('accessible_ai_last_scan', current_time('mysql'));
        }

        wp_send_json_success($result);
    }

    /**
     * Apply a fix via AJAX
     */
    public function apply_fix() {
        check_ajax_referer('accessible_ai_nonce', 'nonce');

        if (!current_user_can('manage_options')) {
            wp_send_json_error(array('message' => 'Permission denied'));
        }

        $issue_id = isset($_POST['issue_id']) ? sanitize_text_field($_POST['issue_id']) : '';
        $fix_code = isset($_POST['fix_code']) ? wp_unslash($_POST['fix_code']) : '';

        if (empty($issue_id) || empty($fix_code)) {
            wp_send_json_error(array('message' => 'Missing required parameters'));
        }

        // For now, we'll store fixes to be applied manually
        // In a full implementation, this would:
        // 1. Parse the fix code to understand what needs to change
        // 2. Apply the changes to the appropriate WordPress content
        // 3. Verify the fix was applied correctly

        // Store the fix for manual review
        $fixes = get_option('accessible_ai_pending_fixes', array());
        $fixes[$issue_id] = array(
            'code' => $fix_code,
            'created_at' => current_time('mysql'),
        );
        update_option('accessible_ai_pending_fixes', $fixes);

        wp_send_json_success(array(
            'message' => __('Fix saved for review. In production, this would be applied automatically.', 'accessible-ai'),
            'fix_code' => $fix_code,
        ));
    }

    /**
     * Poll for scan completion
     */
    public function poll_scan($scan_id, $callback = null) {
        $max_attempts = 60; // 5 minutes max
        $attempt = 0;

        while ($attempt < $max_attempts) {
            $result = $this->api_client->get_scan_results($scan_id);

            if (is_wp_error($result)) {
                return $result;
            }

            if ($result['status'] === 'completed') {
                if ($callback) {
                    call_user_func($callback, $result);
                }
                return $result;
            }

            if ($result['status'] === 'failed') {
                return new WP_Error('scan_failed', $result['error_message'] ?? 'Scan failed');
            }

            sleep(5);
            $attempt++;
        }

        return new WP_Error('scan_timeout', 'Scan timed out');
    }

    /**
     * Get scan history
     */
    public function get_scan_history($limit = 10) {
        return $this->api_client->get_scans($limit);
    }
}
