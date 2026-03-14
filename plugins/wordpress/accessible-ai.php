<?php
/**
 * Plugin Name: AccessibleAI - Accessibility Compliance
 * Plugin URI: https://accessibleai.com/wordpress
 * Description: Automated accessibility scanning and AI-powered fixes for WCAG 2.1 and ADA compliance.
 * Version: 1.0.0
 * Author: AccessibleAI
 * Author URI: https://accessibleai.com
 * License: GPL v2 or later
 * License URI: https://www.gnu.org/licenses/gpl-2.0.html
 * Text Domain: accessible-ai
 * Domain Path: /languages
 * Requires at least: 6.0
 * Requires PHP: 7.4
 */

// Exit if accessed directly
if (!defined('ABSPATH')) {
    exit;
}

// Plugin version
define('ACCESSIBLE_AI_VERSION', '1.0.0');

// Plugin directory paths
define('ACCESSIBLE_AI_PLUGIN_DIR', plugin_dir_path(__FILE__));
define('ACCESSIBLE_AI_PLUGIN_URL', plugin_dir_url(__FILE__));

// Include required files
require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-api-client.php';
require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-scanner.php';
require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-admin.php';
require_once ACCESSIBLE_AI_PLUGIN_DIR . 'includes/class-cron.php';

/**
 * Main AccessibleAI Plugin Class
 */
class Accessible_AI_Plugin {

    /**
     * Single instance of the plugin
     */
    private static $instance = null;

    /**
     * API client instance
     */
    private $api_client;

    /**
     * Scanner instance
     */
    private $scanner;

    /**
     * Admin instance
     */
    private $admin;

    /**
     * Cron instance
     */
    private $cron;

    /**
     * Get single instance
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
     * Load dependencies
     */
    private function load_dependencies() {
        // Initialize API client
        $this->api_client = new Accessible_AI_API_Client();

        // Initialize scanner
        $this->scanner = new Accessible_AI_Scanner($this->api_client);

        // Initialize admin
        $this->admin = new Accessible_AI_Admin($this->api_client, $this->scanner);

        // Initialize cron
        $this->cron = new Accessible_AI_Cron($this->api_client);
    }

    /**
     * Initialize hooks
     */
    private function init_hooks() {
        // Activation hook
        register_activation_hook(__FILE__, array($this, 'activate'));

        // Deactivation hook
        register_deactivation_hook(__FILE__, array($this, 'deactivate'));

        // Load text domain
        add_action('plugins_loaded', array($this, 'load_textdomain'));

        // Enqueue assets
        add_action('admin_enqueue_scripts', array($this, 'enqueue_assets'));

        // Add plugin action links
        add_filter('plugin_action_links_' . plugin_basename(__FILE__), array($this, 'add_action_links'));
    }

    /**
     * Plugin activation
     */
    public function activate() {
        // Set default options
        $defaults = array(
            'accessible_ai_api_key' => '',
            'accessible_ai_site_id' => '',
            'accessible_ai_site_name' => get_bloginfo('name'),
            'accessible_ai_site_url' => home_url(),
            'accessible_ai_platform' => 'wordpress',
            'accessible_ai_auto_scan' => 'weekly',
            'accessible_ai_email_notifications' => '1',
            'accessible_ai_last_scan' => '',
            'accessible_ai_last_score' => '',
            'accessible_ai_widget_enabled' => '1',
        );

        foreach ($defaults as $key => $value) {
            if (get_option($key) === false) {
                add_option($key, $value);
            }
        }

        // Schedule auto-scan
        if (!wp_next_scheduled('accessible_ai_auto_scan_event')) {
            wp_schedule_event(time(), 'daily', 'accessible_ai_auto_scan_event');
        }

        // Create database table for scan results if needed
        $this->create_tables();
    }

    /**
     * Plugin deactivation
     */
    public function deactivate() {
        // Clear scheduled hooks
        wp_clear_scheduled_hook('accessible_ai_auto_scan_event');
    }

    /**
     * Create custom tables
     */
    private function create_tables() {
        global $wpdb;
        $charset_collate = $wpdb->get_charset_collate();
        $table_name = $wpdb->prefix . 'accessibleai_issues';

        $sql = "CREATE TABLE IF NOT EXISTS $table_name (
            id bigint(20) NOT NULL AUTO_INCREMENT,
            scan_id varchar(255) NOT NULL,
            issue_id varchar(255) NOT NULL,
            severity varchar(20) NOT NULL,
            category varchar(100) NOT NULL,
            description text NOT NULL,
            location varchar(255) NOT NULL,
            selector varchar(500),
            fix_generated tinyint(1) DEFAULT 0,
            fix_applied tinyint(1) DEFAULT 0,
            created_at datetime DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (id),
            KEY scan_id (scan_id),
            KEY severity (severity),
            KEY category (category)
        ) $charset_collate;";

        require_once(ABSPATH . 'wp-admin/includes/upgrade.php');
        dbDelta($sql);
    }

    /**
     * Load plugin text domain
     */
    public function load_textdomain() {
        load_plugin_textdomain(
            'accessible-ai',
            false,
            dirname(plugin_basename(__FILE__)) . '/languages/'
        );
    }

    /**
     * Enqueue admin assets
     */
    public function enqueue_assets($hook) {
        // Only load on our admin pages
        if (strpos($hook, 'accessible-ai') === false) {
            return;
        }

        // CSS
        wp_enqueue_style(
            'accessible-ai-admin',
            ACCESSIBLE_AI_PLUGIN_URL . 'assets/css/admin.css',
            array(),
            ACCESSIBLE_AI_VERSION
        );

        // JavaScript
        wp_enqueue_script(
            'accessible-ai-admin',
            ACCESSIBLE_AI_PLUGIN_URL . 'assets/js/admin.js',
            array('jquery'),
            ACCESSIBLE_AI_VERSION,
            true
        );

        // Localize script
        wp_localize_script('accessible-ai-admin', 'accessibleAI', array(
            'ajaxUrl' => admin_url('admin-ajax.php'),
            'nonce' => wp_create_nonce('accessible_ai_nonce'),
            'strings' => array(
                'scanStarted' => __('Scan started successfully!', 'accessible-ai'),
                'scanFailed' => __('Failed to start scan. Please check your API key.', 'accessible-ai'),
                'fixApplied' => __('Fix applied successfully!', 'accessible-ai'),
                'fixFailed' => __('Failed to apply fix.', 'accessible-ai'),
            ),
        ));
    }

    /**
     * Add plugin action links
     */
    public function add_action_links($links) {
        $settings_link = sprintf(
            '<a href="%s">%s</a>',
            admin_url('admin.php?page=accessible-ai-settings'),
            __('Settings', 'accessible-ai')
        );

        array_unshift($links, $settings_link);
        return $links;
    }

    /**
     * Get API client
     */
    public function get_api_client() {
        return $this->api_client;
    }

    /**
     * Get scanner
     */
    public function get_scanner() {
        return $this->scanner;
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

/**
 * Plugin uninstall - cleanup
 */
register_uninstall_hook(__FILE__, 'accessible_ai_uninstall');

function accessible_ai_uninstall() {
    // Delete all options
    $options = array(
        'accessible_ai_api_key',
        'accessible_ai_site_id',
        'accessible_ai_site_name',
        'accessible_ai_site_url',
        'accessible_ai_platform',
        'accessible_ai_auto_scan',
        'accessible_ai_email_notifications',
        'accessible_ai_last_scan',
        'accessible_ai_last_score',
        'accessible_ai_widget_enabled',
        'accessible_ai_last_scheduled_scan',
        'accessible_ai_pending_scan_id',
    );

    foreach ($options as $option) {
        delete_option($option);
    }

    // Drop custom tables
    global $wpdb;
    $table_name = $wpdb->prefix . 'accessibleai_issues';
    $wpdb->query("DROP TABLE IF EXISTS $table_name");
}
