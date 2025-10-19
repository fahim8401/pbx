<?php
/**
 * HPLink PBX WHMCS Server Module
 *
 * Multi-tenant Cloud PBX provisioning module for WHMCS
 */

use WHMCS\Database\Capsule;

if (!defined("WHMCS")) {
    die("This file cannot be accessed directly");
}

/**
 * Module metadata
 */
function hplinkpbx_MetaData()
{
    return [
        'DisplayName' => 'HPLink PBX Cloud',
        'APIVersion' => '1.0',
        'RequiresServer' => true,
        'DefaultNonSSLPort' => '8000',
        'DefaultSSLPort' => '8000',
    ];
}

/**
 * Module configuration options
 */
function hplinkpbx_ConfigOptions()
{
    return [
        'plan_template_id' => [
            'FriendlyName' => 'Plan Template ID',
            'Type' => 'text',
            'Size' => '40',
            'Description' => 'UUID of the plan template to use (leave empty for custom limits)',
        ],
        'extensions_limit' => [
            'FriendlyName' => 'Extensions Limit',
            'Type' => 'text',
            'Size' => '5',
            'Default' => '10',
            'Description' => 'Number of extensions allowed',
        ],
        'did_limit' => [
            'FriendlyName' => 'DID Limit',
            'Type' => 'text',
            'Size' => '5',
            'Default' => '2',
            'Description' => 'Number of DIDs allowed',
        ],
        'concurrency' => [
            'FriendlyName' => 'Concurrent Calls',
            'Type' => 'text',
            'Size' => '5',
            'Default' => '5',
            'Description' => 'Maximum concurrent calls',
        ],
        'recording_rule' => [
            'FriendlyName' => 'Recording Policy',
            'Type' => 'dropdown',
            'Options' => 'none,external,all',
            'Default' => 'none',
            'Description' => 'Call recording policy',
        ],
        'call_direction' => [
            'FriendlyName' => 'Call Direction',
            'Type' => 'dropdown',
            'Options' => 'both,inbound,outbound',
            'Default' => 'both',
            'Description' => 'Allowed call directions',
        ],
        'billing_mode' => [
            'FriendlyName' => 'Billing Mode',
            'Type' => 'dropdown',
            'Options' => 'postpaid,prepaid',
            'Default' => 'postpaid',
            'Description' => 'Billing mode',
        ],
    ];
}

/**
 * Test connection to PBX API
 */
function hplinkpbx_TestConnection(array $params)
{
    try {
        require_once __DIR__ . '/lib/ApiClient.php';
        
        $client = new HPLinkPBX_ApiClient(
            $params['serverhostname'],
            $params['serverusername'],
            $params['serverpassword'],
            $params['serversecure']
        );
        
        $result = $client->get('/health');
        
        if ($result && isset($result['status']) && $result['status'] === 'ok') {
            return [
                'success' => true,
                'error' => '',
            ];
        }
        
        return [
            'success' => false,
            'error' => 'API returned invalid response',
        ];
    } catch (Exception $e) {
        return [
            'success' => false,
            'error' => $e->getMessage(),
        ];
    }
}

/**
 * Create account
 */
function hplinkpbx_CreateAccount(array $params)
{
    try {
        require_once __DIR__ . '/lib/ApiClient.php';
        
        $client = new HPLinkPBX_ApiClient(
            $params['serverhostname'],
            $params['serverusername'],
            $params['serverpassword'],
            $params['serversecure']
        );
        
        // Prepare tenant data
        $tenantData = [
            'name' => $params['clientsdetails']['companyname'] ?: $params['clientsdetails']['firstname'] . ' ' . $params['clientsdetails']['lastname'],
            'domain' => preg_replace('/[^a-z0-9-]/', '', strtolower($params['domain'])),
            'email' => $params['clientsdetails']['email'],
        ];
        
        // Use plan template if provided
        if (!empty($params['configoption1'])) {
            $tenantData['plan_template_id'] = $params['configoption1'];
        } else {
            // Use explicit limits
            $tenantData['limits'] = [
                'extensions_limit' => (int)$params['configoption2'],
                'did_limit' => (int)$params['configoption3'],
                'concurrency' => (int)$params['configoption4'],
                'recording_rule' => $params['configoption5'],
                'call_direction' => $params['configoption6'],
                'billing_mode' => $params['configoption7'],
            ];
        }
        
        // Create tenant
        $result = $client->post('/api/v1/tenants', $tenantData);
        
        if (!$result || !isset($result['id'])) {
            throw new Exception('Failed to create tenant');
        }
        
        // Store mapping in custom table
        hplinkpbx_storeTenantMapping(
            $params['serviceid'],
            $params['clientsdetails']['userid'],
            $result['id'],
            $result['domain'],
            $result['portal_url']
        );
        
        // Store admin credentials in product custom fields
        // (In production, send these via email or store securely)
        
        return 'success';
    } catch (Exception $e) {
        logModuleCall('hplinkpbx', 'CreateAccount', $params, $e->getMessage(), '', [$params['serverpassword']]);
        return $e->getMessage();
    }
}

/**
 * Suspend account
 */
function hplinkpbx_SuspendAccount(array $params)
{
    try {
        require_once __DIR__ . '/lib/ApiClient.php';
        
        $client = new HPLinkPBX_ApiClient(
            $params['serverhostname'],
            $params['serverusername'],
            $params['serverpassword'],
            $params['serversecure']
        );
        
        $mapping = hplinkpbx_getTenantMapping($params['serviceid']);
        if (!$mapping) {
            throw new Exception('Tenant mapping not found');
        }
        
        $result = $client->patch(
            '/api/v1/tenants/' . $mapping->tenant_id,
            ['action' => 'suspend']
        );
        
        return 'success';
    } catch (Exception $e) {
        logModuleCall('hplinkpbx', 'SuspendAccount', $params, $e->getMessage(), '', [$params['serverpassword']]);
        return $e->getMessage();
    }
}

/**
 * Unsuspend account
 */
function hplinkpbx_UnsuspendAccount(array $params)
{
    try {
        require_once __DIR__ . '/lib/ApiClient.php';
        
        $client = new HPLinkPBX_ApiClient(
            $params['serverhostname'],
            $params['serverusername'],
            $params['serverpassword'],
            $params['serversecure']
        );
        
        $mapping = hplinkpbx_getTenantMapping($params['serviceid']);
        if (!$mapping) {
            throw new Exception('Tenant mapping not found');
        }
        
        $result = $client->patch(
            '/api/v1/tenants/' . $mapping->tenant_id,
            ['action' => 'resume']
        );
        
        return 'success';
    } catch (Exception $e) {
        logModuleCall('hplinkpbx', 'UnsuspendAccount', $params, $e->getMessage(), '', [$params['serverpassword']]);
        return $e->getMessage();
    }
}

/**
 * Terminate account
 */
function hplinkpbx_TerminateAccount(array $params)
{
    try {
        require_once __DIR__ . '/lib/ApiClient.php';
        
        $client = new HPLinkPBX_ApiClient(
            $params['serverhostname'],
            $params['serverusername'],
            $params['serverpassword'],
            $params['serversecure']
        );
        
        $mapping = hplinkpbx_getTenantMapping($params['serviceid']);
        if (!$mapping) {
            throw new Exception('Tenant mapping not found');
        }
        
        $result = $client->delete('/api/v1/tenants/' . $mapping->tenant_id);
        
        // Remove mapping
        Capsule::table('mod_hplink_pbx_tenants')
            ->where('service_id', $params['serviceid'])
            ->delete();
        
        return 'success';
    } catch (Exception $e) {
        logModuleCall('hplinkpbx', 'TerminateAccount', $params, $e->getMessage(), '', [$params['serverpassword']]);
        return $e->getMessage();
    }
}

/**
 * Change package/product
 */
function hplinkpbx_ChangePackage(array $params)
{
    try {
        require_once __DIR__ . '/lib/ApiClient.php';
        
        $client = new HPLinkPBX_ApiClient(
            $params['serverhostname'],
            $params['serverusername'],
            $params['serverpassword'],
            $params['serversecure']
        );
        
        $mapping = hplinkpbx_getTenantMapping($params['serviceid']);
        if (!$mapping) {
            throw new Exception('Tenant mapping not found');
        }
        
        // Update limits
        $limits = [
            'extensions_limit' => (int)$params['configoption2'],
            'did_limit' => (int)$params['configoption3'],
            'concurrency' => (int)$params['configoption4'],
            'recording_rule' => $params['configoption5'],
            'call_direction' => $params['configoption6'],
        ];
        
        $result = $client->patch(
            '/api/v1/tenants/' . $mapping->tenant_id,
            ['action' => 'update_limits', 'limits' => $limits]
        );
        
        return 'success';
    } catch (Exception $e) {
        logModuleCall('hplinkpbx', 'ChangePackage', $params, $e->getMessage(), '', [$params['serverpassword']]);
        return $e->getMessage();
    }
}

/**
 * Admin services tab fields
 */
function hplinkpbx_AdminServicesTabFields(array $params)
{
    $mapping = hplinkpbx_getTenantMapping($params['serviceid']);
    
    if (!$mapping) {
        return [];
    }
    
    return [
        'Tenant ID' => $mapping->tenant_id,
        'Domain' => $mapping->domain,
        'Portal URL' => '<a href="' . $mapping->portal_url . '" target="_blank">' . $mapping->portal_url . '</a>',
        'Created' => $mapping->created_at,
    ];
}

/**
 * Usage update (called by WHMCS cron)
 */
function hplinkpbx_UsageUpdate($params)
{
    try {
        require_once __DIR__ . '/lib/ApiClient.php';
        
        $client = new HPLinkPBX_ApiClient(
            $params['serverhostname'],
            $params['serverusername'],
            $params['serverpassword'],
            $params['serversecure']
        );
        
        $mapping = hplinkpbx_getTenantMapping($params['serviceid']);
        if (!$mapping) {
            return;
        }
        
        // Get usage metrics for current billing cycle
        // Determine cycle dates from service
        $service = Capsule::table('tblhosting')
            ->where('id', $params['serviceid'])
            ->first();
        
        if (!$service) {
            return;
        }
        
        $fromDate = $service->billingcycle == 'Monthly' 
            ? date('Y-m-01 00:00:00') 
            : date('Y-m-d 00:00:00', strtotime('-30 days'));
        $toDate = date('Y-m-d 23:59:59');
        
        // Fetch usage from API
        $usage = $client->get(
            '/api/v1/usage/metrics',
            [
                'tenant_id' => $mapping->tenant_id,
                'from_date' => $fromDate,
                'to_date' => $toDate,
            ]
        );
        
        if (!$usage) {
            return;
        }
        
        // Update WHMCS usage metrics
        // These names should match your product's usage billing configuration
        return [
            'minutes_out' => $usage['minutes_out'],
            'minutes_in' => $usage['minutes_in'],
            'storage_gb' => $usage['storage_gb'],
            'sms_count' => $usage['sms_count'],
        ];
    } catch (Exception $e) {
        logModuleCall('hplinkpbx', 'UsageUpdate', $params, $e->getMessage(), '', [$params['serverpassword']]);
    }
}

/**
 * Store tenant mapping in custom table
 */
function hplinkpbx_storeTenantMapping($serviceId, $clientId, $tenantId, $domain, $portalUrl)
{
    Capsule::table('mod_hplink_pbx_tenants')->insert([
        'service_id' => $serviceId,
        'client_id' => $clientId,
        'tenant_id' => $tenantId,
        'domain' => $domain,
        'portal_url' => $portalUrl,
        'created_at' => date('Y-m-d H:i:s'),
        'updated_at' => date('Y-m-d H:i:s'),
    ]);
}

/**
 * Get tenant mapping
 */
function hplinkpbx_getTenantMapping($serviceId)
{
    return Capsule::table('mod_hplink_pbx_tenants')
        ->where('service_id', $serviceId)
        ->first();
}

/**
 * Create custom tables on activation
 */
add_hook('AfterModuleActivate', 1, function($vars) {
    if ($vars['module'] == 'hplinkpbx') {
        $schema = Capsule::schema();
        
        if (!$schema->hasTable('mod_hplink_pbx_tenants')) {
            $schema->create('mod_hplink_pbx_tenants', function ($table) {
                $table->increments('id');
                $table->integer('service_id')->unique();
                $table->integer('client_id');
                $table->string('tenant_id', 40);
                $table->string('domain', 255);
                $table->string('portal_url', 500);
                $table->timestamp('created_at');
                $table->timestamp('updated_at');
            });
        }
    }
});
