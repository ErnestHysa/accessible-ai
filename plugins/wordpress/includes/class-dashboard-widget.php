<?php
/**
 * Dashboard Widget integration
 */

class Accessible_AI_Dashboard_Widget {

    public static function init() {
        add_action('wp_dashboard_setup', array(__CLASS__, 'add_widget'));
    }

    public static function add_widget() {
        if (!current_user_can('manage_options')) {
            return;
        }

        wp_add_dashboard_widget(
            'accessible_ai_widget',
            __('Accessibility Score', 'accessible-ai'),
            array(__CLASS__, 'render_widget')
        );
    }

    public static function render_widget() {
        $score = get_option('accessible_ai_latest_score', null);
        $last_scan = get_option('accessible_ai_last_scan', null);

        if ($score === null) {
            echo '<p>' . esc_html__('No accessibility scan data available.', 'accessible-ai') . '</p>';
            echo '<p><a href="' . admin_url('admin.php?page=accessible-ai-scans') . '" class="button button-primary">' . esc_html__('Run First Scan', 'accessible-ai') . '</a></p>';
            return;
        }

        $score_color = $score >= 90 ? '#22c55e' : ($score >= 70 ? '#eab308' : '#ef4444');
        $score_label = $score >= 90 ? __('Excellent', 'accessible-ai') : ($score >= 70 ? __('Good', 'accessible-ai') : __('Needs Work', 'accessible-ai'));

        ?>
        <div style="text-align: center; padding: 10px 0;">
            <div style="font-size: 48px; font-weight: bold; color: <?php echo esc_attr($score_color); ?>; line-height: 1;">
                <?php echo esc_html($score); ?>
            </div>
            <div style="font-size: 14px; color: <?php echo esc_attr($score_color); ?>; font-weight: 500;">
                <?php echo esc_html($score_label); ?>
            </div>
            <p style="margin: 10px 0 0 0; font-size: 12px; color: #666;">
                <?php printf(__('Accessibility Score', 'accessible-ai')); ?>
            </p>
            <?php if ($last_scan): ?>
                <p style="font-size: 11px; color: #999; margin-top: 5px;">
                    <?php printf(__('Last: %s', 'accessible-ai'), date_i18n(get_option('date_format'), strtotime($last_scan))); ?>
                </p>
            <?php endif; ?>
        </div>
        <p style="text-align: center; margin-top: 15px;">
            <a href="<?php echo admin_url('admin.php?page=accessible-ai-scans'); ?>" class="button">
                <?php esc_html_e('View Details', 'accessible-ai'); ?>
            </a>
        </p>
        <?php
    }
}

// Initialize dashboard widget
Accessible_AI_Dashboard_Widget::init();
