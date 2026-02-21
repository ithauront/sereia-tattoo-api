def render_vip_account_created_email(client_code: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Conta VIP criada</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:6px;padding:32px;">
          
          <tr>
            <td style="text-align:center;">
              <h2 style="margin-bottom:16px;color:#222;">
                🎉 Sua conta VIP foi criada
              </h2>
            </td>
          </tr>

          <tr>
            <td style="color:#444;font-size:14px;line-height:1.6;">
              <p>
                Sua conta VIP no <strong>Sereia Tattoo Studio</strong> foi criada com sucesso.
              </p>

              <p>
                Nesse e-mail você encontrara seu código VIP!
                <br/>
                Indique nossos serviços para amigos usando esse código para desbloquear benefícios exclusivos do programa VIP!
              </p>
            </td>
          </tr>

          <tr>
            <td align="center" style="padding:16px 0;">
              <div style="
                background:#f0f0f0;
                border:1px dashed #ccc;
                padding:16px;
                border-radius:6px;
                text-align:center;
                font-size:14px;
                color:#333;
              ">
                <p style="margin:0 0 8px 0;">Seu <strong>Client Code</strong>:</p>
                <p style="margin:0;font-size:20px;font-weight:bold;letter-spacing:1px;">
                  {client_code}
                </p>
              </div>
            </td>
          </tr>

          <tr>
            <td style="color:#444;font-size:14px;line-height:1.6;padding-top:16px;">
              <p>
                Guarde este código com segurança. Ele pode ser solicitado para suporte ou identificação da sua conta.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#999;font-size:11px;text-align:center;">
              <p>
                Se você não reconhece esta conta, entre em contato conosco imediatamente.
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()
