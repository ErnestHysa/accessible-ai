<?php
/**
 * Plugin Name: AccessibleAI - Accessibility Compliance
 * Plugin URI: https://accessibleai.com
 * Description: AI-powered accessibility scanning and fixes for WCAG 2.1 compliance.
 * Version: 1.0.0
 * Author: AccessibleAI
 * Author URI: https://accessibleai.com
 * License: GPL v2 or later
 * Text Domain: accessible-ai
 * Domain Path: /languages
 */

// Prevent direct access
if (!defined('ABSPATH')) {
    exit;
}

// Plugin version
define('ACCESSIBLE_AI_VERSION', '1.0.0');
define('ACCESSIBLE_AI_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('ACCESSIBLE_AI_PLUGIN_URL', plugin_dir_url(__FILE__));
define('ACCESSIBLE_AI_API_BASE', get_option('accessible_ai_api_url', 'https://api.accessibleai.com'));

/**
 * Main plugin class
 */
class Accessible_AI_Plugin {

    private static $instance = null;
    private $api_client = null;
    private $scanner = null;
    private $admin = null;

    /**
     * Get singleton instance
     */
    public static function get_instance() {
        if (null === self::$instance) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Constructor
     */
    private function __construct() {
        $this->load_dependencies();
        $this->init_hooks();
    }

    /**
     * Load required files
     */
    private function load_dependencies() {
        require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-api-client.php';
        require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-scanner.php';
        require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-admin.php';
        require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-dashboard-widget.php';

        $this->api_client = new Accessible_AI_API_Client();
        $this->scanner = new Accessible_AI_Scanner($this->api_client);
        $this->admin = new Accessible_AI_Admin($this->api_client);
    }

    /**
     * Initialize hooks
     */
    private function init_hooks() {
        register_activation_hook(__FILE__, array($this, 'activate'));
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        add_action('plugins_loaded', array($this, 'load_textdomain'));
        add_action('admin_enqueue_scripts', array($this, 'enqueue_admin_assets'));
        add_action('wp_ajax_accessible_ai_save_settings', array($this->admin, 'save_settings'));
        add_action('wp_ajax_accessible_ai_run_scan', array($this->scanner, 'run_scan'));
        add_action('wp_ajax_accessible_ai_get_scan_results', array($this->scanner, 'get_scan_results'));
        add_action('wp_ajax_accessible_ai_apply_fix', array($this->scanner, 'apply_fix'));
    }

    /**
     * Load plugin text domain
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'accessible-ai',
            false,
            dirname(plugin_basename(__FILE__)) . '/languages'
        );
    }

    /**
     * Enqueue admin assets
     */
    public function enqueue_admin_assets($hook) {
        // Only load on our admin pages
        if (strpos($hook, 'accessible-ai') === false) {
            return;
        }

        wp_enqueue_style(
            'accessible-ai-admin',
            ACCESSIBLE_AI_PLUGIN_URL . 'assets/css/admin.css',
            array(),
            ACCESSIBLE_AI_VERSION
        );

        wp_enqueue_script(
            'accessible-ai-admin',
            ACCESSIBLE_AI_PLUGIN_URL . 'assets/js/admin.js',
            array('jquery'),
            ACCESSIBLE_AI_VERSION,
            true
        );

        wp_localize_script('accessible-ai-admin', 'accessibleAI', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('accessible_ai_nonce'),
            'apiUrl' => ACCESSIBLE_AI_API_BASE,
            'siteUrl' => get_site_url(),
        ));
    }

    /**
     * Plugin activation
     */
    public function activate() {
        // Set default options
        $default_options = array(
            'accessible_ai_api_key' => '',
            'accessible_ai_api_url' => 'https://api.accessibleai.com',
            'accessible_ai_auto_scan' => 'weekly',
            'accessible_ai_show_badge' => '1',
        );

        foreach ($default_options as $option => $value) {
            if (get_option($option) === false) {
                add_option($option, $value);
            }
        }

        // Schedule WP-Cron for auto-scans
        if (!wp_next_scheduled('accessible_ai_auto_scan')) {
            wp_schedule_event(time(), 'daily', 'accessible_ai_auto_scan');
        }
    }

    /**
     * Plugin deactivation
     */
    public function deactivate() {
        // Clear scheduled hooks
        wp_clear_scheduled_hook('accessible_ai_auto_scan');
    }
}

/**
 * Initialize the plugin
 */
function accessible_ai_init() {
    return Accessible_AI_Plugin::get_instance();
}

// Start the plugin
accessible_ai_init();
