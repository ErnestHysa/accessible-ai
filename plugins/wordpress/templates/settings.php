<?php
/**
 * AccessibleAI Settings Template
 */

$api_key = get_option('accessible_ai_api_key', '');
$api_url = get_option('accessible_ai_api_url', 'https://api.accessibleai.com');
$auto_scan = get_option('accessible_ai_auto_scan', 'weekly');
$show_badge = get_option('accessible_ai_show_badge', '1');
?>

<div class="wrap accessible-ai-settings">
    <h1><?php esc_html_e('AccessibleAI Settings', 'accessible-ai'); ?></h1>

    <form method="post" action="">
        <?php wp_nonce_field('accessible_ai_settings'); ?>

        <table class="form-table">
            <tr>
                <th scope="row">
                    <label for="api_key"><?php esc_html_e('API Key', 'accessible-ai'); ?></label>
                </th>
                <td>
                    <input type="password"
                           name="api_key"
                           id="api_key"
                           value="<?php echo esc_attr($api_key); ?>"
                           class="regular-text"
                           required />
                    <p class="description">
                        <?php
                        printf(
                            __('Get your API key from the %sAccessibleAI Dashboard%s.', 'accessible-ai'),
                            '<a href="https://accessibleai.com/dashboard" target="_blank">',
                            '</a>'
                        );
                        ?>
                    </p>
                </td>
            </tr>

            <tr>
                <th scope="row">
                    <label for="api_url"><?php esc_html_e('API URL', 'accessible-ai'); ?></label>
                </th>
                <td>
                    <input type="url"
                           name="api_url"
                           id="api_url"
                           value="<?php echo esc_attr($api_url); ?>"
                           class="regular-text" />
                    <p class="description">
                        <?php esc_html_e('The API endpoint URL. Only change if using a self-hosted instance.', 'accessible-ai'); ?>
                    </p>
                </td>
            </tr>

            <tr>
                <th scope="row">
                    <label for="auto_scan"><?php esc_html_e('Auto-Scan Frequency', 'accessible-ai'); ?></label>
                </th>
                <td>
                    <select name="auto_scan" id="auto_scan">
                        <option value="disabled" <?php selected($auto_scan, 'disabled'); ?>>
                            <?php esc_html_e('Disabled', 'accessible-ai'); ?>
                        </option>
                        <option value="daily" <?php selected($auto_scan, 'daily'); ?>>
                            <?php esc_html_e('Daily', 'accessible-ai'); ?>
                        </option>
                        <option value="weekly" <?php selected($auto_scan, 'weekly'); ?>>
                            <?php esc_html_e('Weekly', 'accessible-ai'); ?>
                        </option>
                        <option value="monthly" <?php selected($auto_scan, 'monthly'); ?>>
                            <?php esc_html_e('Monthly', 'accessible-ai'); ?>
                        </option>
                    </select>
                    <p class="description">
                        <?php esc_html_e('How often to automatically scan your site for accessibility issues.', 'accessible-ai'); ?>
                    </p>
                </td>
            </tr>

            <tr>
                <th scope="row">
                    <label for="show_badge"><?php esc_html_e('Show Accessibility Badge', 'accessible-ai'); ?></label>
                </th>
                <td>
                    <label>
                        <input type="checkbox"
                               name="show_badge"
                               id="show_badge"
                               value="1"
                               <?php checked($show_badge, '1'); ?> />
                        <?php esc_html_e('Display accessibility score badge on your site', 'accessible-ai'); ?>
                    </label>
                    <p class="description">
                        <?php esc_html_e('Shows a floating badge with your accessibility score in the corner of your site.', 'accessible-ai'); ?>
                    </p>
                </td>
            </tr>
        </table>

        <?php submit_button(__('Save Settings', 'accessible-ai'), 'primary', 'accessible_ai_save_settings'); ?>
    </form>

    <hr>

    <h2><?php esc_html_e('Connection Status', 'accessible-ai'); ?></h2>
    <div id="connection-status">
        <p class="spinner is-active" style="float: none;"></p>
    </div>

    <script>
    jQuery(document).ready(function($) {
        // Test connection
        function testConnection() {
            $('#connection-status').html('<p class="spinner is-active" style="float: none;"></p>');

            $.ajax({
                url: ajaxurl,
                type: 'POST',
                data: {
                    action: 'accessible_ai_test_connection',
                    nonce: accessibleAI.nonce
                },
                success: function(response) {
                    if (response.success) {
                        $('#connection-status').html(
                            '<div class="notice notice-success inline"><p>' +
                            '<span class="dashicons dashicons-yes"></span> ' +
                            '<?php esc_html_e('Connected successfully!', 'accessible-ai'); ?> ' +
                            '</p></div>'
                        );
                    } else {
                        $('#connection-status').html(
                            '<div class="notice notice-error inline"><p>' +
                            '<span class="dashicons dashicons-no"></span> ' +
                            '<?php esc_html_e('Connection failed. Please check your API key.', 'accessible-ai'); ?> ' +
                            '</p></div>'
                        );
                    }
                },
                error: function() {
                    $('#connection-status').html(
                        '<div class="notice notice-error inline"><p>' +
                        '<span class="dashicons dashicons-no"></span> ' +
                        '<?php esc_html_e('Connection failed. Please check your API key.', 'accessible-ai'); ?> ' +
                        '</p></div>'
                    );
                }
            });
        }

        testConnection();
    });
    </script>

    <hr>

    <h2><?php esc_html_e('Resources', 'accessible-ai'); ?></h2>
    <ul>
        <li>
            <a href="https://accessibleai.com/docs" target="_blank">
                <?php esc_html_e('Documentation', 'accessible-ai'); ?>
            </a>
        </li>
        <li>
            <a href="https://accessibleai.com/support" target="_blank">
                <?php esc_html_e('Support', 'accessible-ai'); ?>
            </a>
        </li>
        <li>
            <a href="https://www.w3.org/WAI/WCAG21/quickref/" target="_blank">
                <?php esc_html_e('WCAG 2.1 Quick Reference', 'accessible-ai'); ?>
            </a>
        </li>
    </ul>
</div>
