def render_account_activated_email() -> str:
    return """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Conta ativada</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:6px;padding:32px;">
          
          <tr>
            <td style="text-align:center;">
              <h2 style="margin-bottom:16px;color:#222;">
                ✅ Sua conta foi ativada
              </h2>
            </td>
          </tr>

          <tr>
            <td style="color:#444;font-size:14px;line-height:1.6;">
              <p>
                Parabéns! Sua conta no <strong>Sereia Tattoo Studio</strong> foi ativada com sucesso.
              </p>

              <p>
                Agora você já pode utilizar nossos serviços e gerenciar sua conta normalmente.
              </p>

              <p>
                Estamos felizes em ter você conosco! ✨
              </p>
            </td>
          </tr>

          <tr>
            <td style="color:#444;font-size:14px;line-height:1.6;padding-top:16px;">
              <p>
                Se você não realizou esta ação ou acredita que houve algum erro, entre em contato com nosso suporte.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#999;font-size:11px;text-align:center;">
              <p>
                Este é um e-mail automático. Caso precise de ajuda, entre em contato conosco.
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
