<?php
/**
 * Admin interface for AccessibleAI
 */

class Accessible_AI_Admin {

    private $api_client;

    public function __construct($api_client) {
        $this->api_client = $api_client;

        add_action('admin_menu', array($this, 'add_admin_menu'));
        add_action('admin_notices', array($this, 'admin_notices'));
        add_action('wp_dashboard_setup', array($this, 'add_dashboard_widget'));
    }

    /**
     * Add admin menu items
     */
    public function add_admin_menu() {
        add_menu_page(
            __('AccessibleAI', 'accessible-ai'),
            __('Accessibility', 'accessible-ai'),
            'manage_options',
            'accessible-ai',
            array($this, 'render_dashboard'),
            'dashicons-universal-access-alt',
            30
        );

        add_submenu_page(
            'accessible-ai',
            __('Dashboard', 'accessible-ai'),
            __('Dashboard', 'accessible-ai'),
            'manage_options',
            'accessible-ai',
            array($this, 'render_dashboard')
        );

        add_submenu_page(
            'accessible-ai',
            __('Scans', 'accessible-ai'),
            __('Scans', 'accessible-ai'),
            'manage_options',
            'accessible-ai-scans',
            array($this, 'render_scans')
        );

        add_submenu_page(
            'accessible-ai',
            __('Settings', 'accessible-ai'),
            __('Settings', 'accessible-ai'),
            'manage_options',
            'accessible-ai-settings',
            array($this, 'render_settings')
        );
    }

    /**
     * Add dashboard widget
     */
    public function add_dashboard_widget() {
        if (!current_user_can('manage_options')) {
            return;
        }
        wp_add_dashboard_widget(
            'accessible_ai_widget',
            __('Accessibility Score', 'accessible-ai'),
            array($this, 'render_dashboard_widget')
        );
    }

    /**
     * Render dashboard widget
     */
    public function render_dashboard_widget() {
        $score = get_option('accessible_ai_latest_score', null);
        $last_scan = get_option('accessible_ai_last_scan', null);

        if ($score === null) {
            echo '<p>' . esc_html__('No scans yet. Run your first scan to see your accessibility score.', 'accessible-ai') . '</p>';
            echo '<p><a href="' . admin_url('admin.php?page=accessible-ai-scans') . '" class="button button-primary">' . esc_html__('Run Scan', 'accessible-ai') . '</a></p>';
            return;
        }

        $score_color = $score >= 90 ? 'green' : ($score >= 70 ? 'yellow' : 'red');
        echo '<div class="accessible-ai-score" style="text-align: center;">';
        echo '<div style="font-size: 48px; font-weight: bold; color: ' . esc_attr($score_color) . ';">' . esc_html($score) . '/100</div>';
        echo '<p>' . esc_html__('Accessibility Score', 'accessible-ai') . '</p>';
        if ($last_scan) {
            echo '<p style="font-size: 12px; color: #666;">' . sprintf(__('Last scanned: %s', 'accessible-ai'), date_i18n(get_option('date_format'), $last_scan)) . '</p>';
        }
        echo '</div>';
        echo '<p><a href="' . admin_url('admin.php?page=accessible-ai-scans') . '" class="button">' . esc_html__('View Details', 'accessible-ai') . '</a></p>';
    }

    /**
     * Show admin notices
     */
    public function admin_notices() {
        // Show if API key is not set
        if (empty(get_option('accessible_ai_api_key'))) {
            $screen = get_current_screen();
            if (isset($screen->id) && strpos($screen->id, 'accessible-ai') === false) {
                echo '<div class="notice notice-warning is-dismissible">';
                echo '<p>' . sprintf(__('AccessibleAI is almost ready! <a href="%s">Connect your API key</a> to start scanning for accessibility issues.', 'accessible-ai'), admin_url('admin.php?page=accessible-ai-settings')) . '</p>';
                echo '</div>';
            }
        }
    }

    /**
     * Render dashboard page
     */
    public function render_dashboard() {
        $score = get_option('accessible_ai_latest_score', null);
        $last_scan = get_option('accessible_ai_last_scan', null);
        $site_id = get_option('accessible_ai_site_id', '');

        include ACCESSIBLE_AI_PLUGIN_DIR . 'templates/dashboard.php';
    }

    /**
     * Render scans page
     */
    public function render_scans() {
        $scans = get_option('accessible_ai_scan_history', array());
        include ACCESSIBLE_AI_PLUGIN_DIR . 'templates/scans.php';
    }

    /**
     * Render settings page
     */
    public function render_settings() {
        if (isset($_POST['accessible_ai_save_settings']) && check_admin_referer('accessible_ai_settings')) {
            $api_key = sanitize_text_field($_POST['api_key'] ?? '');
            $api_url = sanitize_text_field($_POST['api_url'] ?? 'https://api.accessibleai.com');
            $auto_scan = sanitize_text_field($_POST['auto_scan'] ?? 'weekly');
            $show_badge = isset($_POST['show_badge']) ? '1' : '0';

            update_option('accessible_ai_api_key', $api_key);
            update_option('accessible_ai_api_url', $api_url);
            update_option('accessible_ai_auto_scan', $auto_scan);
            update_option('accessible_ai_show_badge', $show_badge);

            // Test connection
            if (!empty($api_key)) {
                $this->api_client->set_credentials($api_key, $api_url);
                echo '<div class="notice notice-success"><p>' . esc_html__('Settings saved and connection tested!', 'accessible-ai') . '</p></div>';
            } else {
                echo '<div class="notice notice-success"><p>' . esc_html__('Settings saved.', 'accessible-ai') . '</p></div>';
            }
        }

        $api_key = get_option('accessible_ai_api_key', '');
        $api_url = get_option('accessible_ai_api_url', 'https://api.accessibleai.com');
        $auto_scan = get_option('accessible_ai_auto_scan', 'weekly');
        $show_badge = get_option('accessible_ai_show_badge', '1');

        include ACCESSIBLE_AI_PLUGIN_DIR . 'templates/settings.php';
    }
}
