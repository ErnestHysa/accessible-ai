<?php
/**
 * API Client for communicating with AccessibleAI SaaS
 */

class Accessible_AI_API_Client {

    private $api_key;
    private $api_url;
    private $site_id;

    public function __construct() {
        $this->api_key = get_option('accessible_ai_api_key', '');
        $this->api_url = get_option('accessible_ai_api_url', 'https://api.accessibleai.com');
        $this->site_id = get_option('accessible_ai_site_id', '');
    }

    /**
     * Make API request
     */
    private function request($endpoint, $method = 'GET', $data = array()) {
        $url = rtrim($this->api_url, '/') . '/' . ltrim($endpoint, '/');

        $args = array(
            'method' => $method,
            'headers' => array(
                'Authorization' => 'Bearer ' . $this->api_key,
                'Content-Type' => 'application/json',
            ),
            'timeout' => 30,
        );

        if (!empty($data) && in_array($method, array('POST', 'PUT', 'PATCH'))) {
            $args['body'] = json_encode($data);
        }

        $response = wp_remote_request($url, $args);

        if (is_wp_error($response)) {
            return new WP_Error('api_error', $response->get_error_message());
        }

        $body = wp_remote_retrieve_body($response);
        $code = wp_remote_retrieve_response_code($response);

        if ($code >= 400) {
            return new WP_Error('api_error', sprintf('API Error (%d): %s', $code, $body));
        }

        return json_decode($body, true);
    }

    /**
     * Register/connect this WordPress site
     */
    public function register_site() {
        $data = array(
            'url' => get_site_url(),
            'name' => get_bloginfo('name'),
            'platform' => 'wordpress',
            'version' => ACCESSIBLE_AI_VERSION,
        );

        return $this->request('/api/v1/websites', 'POST', $data);
    }

    /**
     * Trigger a scan
     */
    public function trigger_scan($full_scan = false) {
        if (empty($this->site_id)) {
            return new WP_Error('no_site_id', 'Site not registered. Please connect your API key.');
        }

        $data = array(
            'full_scan' => $full_scan,
            'max_pages' => 50,
        );

        return $this->request('/api/v1/websites/' . $this->site_id . '/scan', 'POST', $data);
    }

    /**
     * Get scan results
     */
    public function get_scan_results($scan_id) {
        return $this->request('/api/v1/scans/' . $scan_id, 'GET');
    }

    /**
     * Get issues for a scan
     */
    public function get_scan_issues($scan_id, $severity = null) {
        $endpoint = '/api/v1/scans/' . $scan_id . '/issues';
        if ($severity) {
            $endpoint .= '?severity=' . $severity;
        }
        return $this->request($endpoint, 'GET');
    }

    /**
     * Get fix for an issue
     */
    public function get_fix($issue_id) {
        return $this->request('/api/v1/scans/issues/' . $issue_id . '/fix', 'POST', array(
            'auto_apply' => false,
        ));
    }

    /**
     * Apply a fix (auto-apply if possible)
     */
    public function apply_fix($issue_id) {
        return $this->request('/api/v1/scans/issues/' . $issue_id . '/fix', 'POST', array(
            'auto_apply' => true,
        ));
    }

    /**
     * Get latest scans
     */
    public function get_scans($limit = 10) {
        $endpoint = '/api/v1/scans?limit=' . intval($limit);
        if (!empty($this->site_id)) {
            $endpoint .= '&website_id=' . $this->site_id;
        }
        return $this->request($endpoint, 'GET');
    }

    /**
     * Test API connection
     */
    public function test_connection() {
        // Try to get current user info
        return $this->request('/api/v1/auth/me', 'GET');
    }

    /**
     * Update API credentials
     */
    public function set_credentials($api_key, $api_url = null) {
        $this->api_key = $api_key;
        if ($api_url) {
            $this->api_url = $api_url;
        }

        update_option('accessible_ai_api_key', $api_key);
        if ($api_url) {
            update_option('accessible_ai_api_url', $api_url);
        }

        // Test connection and register site
        $result = $this->test_connection();

        if (!is_wp_error($result)) {
            // Register this site if not already
            if (empty($this->site_id)) {
                $site = $this->register_site();
                if (!is_wp_error($site) && isset($site['id'])) {
                    update_option('accessible_ai_site_id', $site['id']);
                    $this->site_id = $site['id'];
                }
            }
            return true;
        }

        return $result;
    }
}
