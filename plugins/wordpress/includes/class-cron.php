<?php
/**
 * WP-Cron integration for automated scanning
 */

class Accessible_AI_Cron {

    private $plugin_file;
    private $api_client;

    public function __construct($api_client) {
        $this->plugin_file = ACCESSIBLE_AI_PLUGIN_DIR . 'accessible-ai.php';
        $this->api_client = $api_client;

        // Schedule hooks
        add_action('wp', array($this, 'schedule_auto_scan'));
        add_action('accessible_ai_auto_scan_event', array($this, 'run_scheduled_scan'));
    }

    /**
     * Schedule automated scanning based on settings
     */
    public function schedule_auto_scan() {
        $frequency = get_option('accessible_ai_auto_scan', 'weekly');

        // Clear existing schedule
        wp_clear_scheduled_hook('accessible_ai_auto_scan_event');

        // Skip if disabled
        if ($frequency === 'disabled') {
            return;
        }

        // Schedule based on frequency
        $schedules = array(
            'daily' => 'daily',
            'weekly' => 'weekly',
            'monthly' => 'monthly',
        );

        if (isset($schedules[$frequency])) {
            wp_schedule_event(time(), $schedules[$frequency], 'accessible_ai_auto_scan_event');
        }
    }

    /**
     * Run the scheduled scan
     */
    public function run_scheduled_scan() {
        // Check if API is connected
        if (empty(get_option('accessible_ai_api_key'))) {
            error_log('AccessibleAI: Cannot run auto-scan, API key not configured');
            return;
        }

        // Get all websites registered
        $site_id = get_option('accessible_ai_site_id', '');
        if (empty($site_id)) {
            error_log('AccessibleAI: Cannot run auto-scan, site not registered');
            return;
        }

        // Trigger scan via API
        $result = $this->api_client->trigger_scan(false);

        if (is_wp_error($result)) {
            error_log('AccessibleAI: Auto-scan failed - ' . $result->get_error_message());
            return;
        }

        // Store scan ID for later tracking
        update_option('accessible_ai_last_scheduled_scan', current_time('mysql'));
        update_option('accessible_ai_pending_scan_id', $result['scan_id']);

        // Log success
        error_log('AccessibleAI: Auto-scan triggered successfully - Scan ID: ' . $result['scan_id']);

        // Optionally send notification
        $this->send_scan_notification($result['scan_id']);
    }

    /**
     * Send notification when scan is complete
     */
    private function send_scan_notification($scan_id) {
        $admin_email = get_option('admin_email', '');

        if (empty($admin_email) || !get_option('accessible_ai_email_notifications', '1')) {
            return;
        }

        // Poll for scan completion (in a real implementation, this would be a background job)
        $scan_complete = $this->wait_for_scan_completion($scan_id, 300); // 5 minutes max

        if (!$scan_complete) {
            return;
        }

        // Get scan results
        $result = $this->api_client->get_scan_results($scan_id);

        if (is_wp_error($result)) {
            return;
        }

        $score = $result['score'] ?? 0;
        $total_issues = $result['total_issues'] ?? 0;

        // Send email using WordPress mail function
        $subject = sprintf(__('Accessibility Scan Complete - Score: %d/100', 'accessible-ai'), $score);
        $message = sprintf(
            __('Your website has been scanned for accessibility issues.

Score: %d/100
Total Issues: %d

View details: %s', 'accessible-ai'),
            $score,
            $total_issues,
            admin_url('admin.php?page=accessible-ai-scans')
        );

        wp_mail($admin_email, $subject, $message);
    }

    /**
     * Wait for scan to complete
     */
    private function wait_for_scan_completion($scan_id, $timeout = 300) {
        $start_time = time();
        $attempts = 0;
        $max_attempts = $timeout / 10; // Check every 10 seconds

        while ($attempts < $max_attempts) {
            $result = $this->api_client->get_scan_results($scan_id);

            if (is_wp_error($result)) {
                $attempts++;
                sleep(10);
                continue;
            }

            if ($result['status'] === 'completed') {
                return true;
            }

            if ($result['status'] === 'failed') {
                return false;
            }

            $attempts++;
            sleep(10);
        }

        return false;
    }

    /**
     * Add manual scan interval option
     */
    public function add_manual_scan_interval() {
        register_setting('accessible_ai_scan_interval', array(
            'type' => 'number',
            'label' => __('Hours between manual auto-scans', 'accessible-ai'),
            'default' => 168, // 1 week
            'description' => __('Minimum time between automatic scans (in hours).', 'accessible-ai'),
        ));
    }

    /**
     * Get next scheduled scan time
     */
    public function get_next_scan_time() {
        $next_scheduled = wp_next_scheduled('accessible_ai_auto_scan_event');

        if ($next_scheduled === false) {
            return __('Not scheduled', 'accessible-ai');
        }

        $next_scan_time = $next_scheduled - time();

        if ($next_scan_time < 0) {
            return __('Overdue', 'accessible-ai');
        }

        $hours = floor($next_scan_time / 3600);
        $minutes = floor(($next_scan_time % 3600) / 60);

        if ($hours > 48) {
            $days = floor($hours / 24);
            return sprintf(__('in %d days', 'accessible-ai'), $days);
        } elseif ($hours > 0) {
            return sprintf(__('in %d hours %d minutes', 'accessible-ai'), $hours, $minutes);
        } else {
            return sprintf(__('in %d minutes', 'accessible-ai'), $minutes);
        }
    }

    /**
     * Display next scan time in admin
     */
    public function display_next_scan_time() {
        echo '<p>' . esc_html($this->get_next_scan_time()) . '</p>';
    }
}
