def render_password_reset_email(reset_link: str) -> str:
    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <title>Recuperação de senha</title>
</head>
<body style="margin:0;padding:0;font-family:Arial,Helvetica,sans-serif;background-color:#f5f5f5;">
  <table width="100%" cellpadding="0" cellspacing="0">
    <tr>
      <td align="center" style="padding:40px 16px;">
        <table width="100%" cellpadding="0" cellspacing="0" style="max-width:480px;background:#ffffff;border-radius:6px;padding:32px;">
          
          <tr>
            <td style="text-align:center;">
              <h2 style="margin-bottom:16px;color:#222;">
                Redefina sua senha
              </h2>
            </td>
          </tr>

          <tr>
            <td style="color:#444;font-size:14px;line-height:1.6;">
              <p>
                Recebemos uma solicitação para redefinir a senha da sua conta no <strong>Sereia Tattoo</strong>.
              </p>

              <p>
                Para criar uma nova senha, clique no botão abaixo:
              </p>
            </td>
          </tr>

          <tr>
            <td align="center" style="padding:24px 0;">
              <a href="{reset_link}"
                 style="
                   background:#111;
                   color:#ffffff;
                   padding:12px 20px;
                   text-decoration:none;
                   border-radius:4px;
                   font-size:14px;
                   display:inline-block;
                 ">
                Redefinir minha senha
              </a>
            </td>
          </tr>

          <tr>
            <td style="color:#666;font-size:12px;line-height:1.5;">
              <p>
                Se o botão não funcionar, copie e cole o link abaixo no seu navegador:
              </p>

              <p style="word-break:break-all;">
                <a href="{reset_link}" style="color:#555;">
                  {reset_link}
                </a>
              </p>

              <p>
                Este link é válido por apenas 15 minutos.
              </p>
            </td>
          </tr>

          <tr>
            <td style="padding-top:24px;color:#999;font-size:11px;text-align:center;">
              <p>
                Se você não solicitou a redefinição de senha, pode ignorar este email com segurança.
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
