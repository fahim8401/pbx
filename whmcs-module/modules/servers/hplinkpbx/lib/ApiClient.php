<?php
/**
 * HPLink PBX API Client with HMAC Authentication
 */

class HPLinkPBX_ApiClient
{
    private $baseUrl;
    private $username;
    private $secret;
    private $secure;

    public function __construct($hostname, $username, $secret, $secure = true)
    {
        $protocol = $secure ? 'https' : 'http';
        $this->baseUrl = $protocol . '://' . $hostname;
        $this->username = $username;
        $this->secret = $secret;
        $this->secure = $secure;
    }

    /**
     * Make GET request
     */
    public function get($path, $params = [])
    {
        $url = $this->baseUrl . $path;
        
        if (!empty($params)) {
            $url .= '?' . http_build_query($params);
        }
        
        return $this->request('GET', $path, null);
    }

    /**
     * Make POST request
     */
    public function post($path, $data)
    {
        return $this->request('POST', $path, $data);
    }

    /**
     * Make PUT request
     */
    public function put($path, $data)
    {
        return $this->request('PUT', $path, $data);
    }

    /**
     * Make PATCH request
     */
    public function patch($path, $data)
    {
        return $this->request('PATCH', $path, $data);
    }

    /**
     * Make DELETE request
     */
    public function delete($path)
    {
        return $this->request('DELETE', $path, null);
    }

    /**
     * Make HTTP request with HMAC authentication
     */
    private function request($method, $path, $data = null)
    {
        $timestamp = time();
        $body = $data ? json_encode($data) : '';
        $bodyHash = hash('sha256', $body);
        
        // HMAC signature: HMAC-SHA256(SECRET, USER|METHOD|PATH|TIMESTAMP|SHA256(body))
        $message = $this->username . '|' . $method . '|' . $path . '|' . $timestamp . '|' . $bodyHash;
        $signature = hash_hmac('sha256', $message, $this->secret);
        
        $headers = [
            'X-PBX-API-USER: ' . $this->username,
            'X-PBX-TIMESTAMP: ' . $timestamp,
            'X-PBX-SIGNATURE: ' . $signature,
            'Content-Type: application/json',
        ];
        
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $this->baseUrl . $path);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        
        if ($data) {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $body);
        }
        
        if (!$this->secure) {
            curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
            curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        }
        
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        $error = curl_error($ch);
        curl_close($ch);
        
        // Log the request
        logModuleCall(
            'hplinkpbx',
            $method . ' ' . $path,
            $data,
            $response,
            $httpCode,
            [$this->secret]
        );
        
        if ($error) {
            throw new Exception('HTTP Error: ' . $error);
        }
        
        if ($httpCode >= 400) {
            throw new Exception('API Error: HTTP ' . $httpCode . ' - ' . $response);
        }
        
        return json_decode($response, true);
    }
}
