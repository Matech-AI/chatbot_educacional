import React from "react";
import { Link } from "react-router-dom";

const PrivacyPolicyPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="mb-8">
          <Link
            to="/"
            className="text-sm text-blue-600 hover:underline"
          >
            ← Voltar ao início
          </Link>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Política de Privacidade
          </h1>
          <p className="text-sm text-gray-500 mb-8">
            Última atualização: 31 de maio de 2026
          </p>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              1. Quem somos
            </h2>
            <p className="text-gray-600 leading-relaxed">
              O <strong>DNA da Força</strong> (
              <a
                href="https://iadnadaforca.com.br"
                className="text-blue-600 hover:underline"
              >
                iadnadaforca.com.br
              </a>
              ) é uma plataforma educacional com assistente de inteligência
              artificial, voltada ao apoio de alunos e instrutores em
              diferentes áreas do conhecimento. Este documento descreve como
              coletamos, usamos e protegemos os seus dados pessoais.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              2. Dados que coletamos
            </h2>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>
                <strong>Dados de cadastro:</strong> nome completo, endereço de
                e-mail e nome de usuário fornecidos no momento do registro.
              </li>
              <li>
                <strong>Dados de autenticação:</strong> credenciais de acesso
                (senha armazenada de forma criptografada) e, quando aplicável,
                dados provenientes do login via Google (nome e e-mail da conta
                Google).
              </li>
              <li>
                <strong>Dados de uso:</strong> histórico de interações com o
                assistente de IA e materiais acessados, para fins de melhoria
                contínua da plataforma.
              </li>
              <li>
                <strong>Dados técnicos:</strong> endereço IP, tipo de
                navegador e horário de acesso, coletados automaticamente para
                fins de segurança e diagnóstico.
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              3. Como usamos seus dados
            </h2>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Permitir o acesso à plataforma e autenticar usuários.</li>
              <li>
                Personalizar a experiência educacional dentro da plataforma.
              </li>
              <li>Enviar comunicações relacionadas à conta (ex.: redefinição de senha).</li>
              <li>Garantir a segurança e o bom funcionamento da plataforma.</li>
              <li>Cumprir obrigações legais aplicáveis.</li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              4. Login com Google (OAuth 2.0)
            </h2>
            <p className="text-gray-600 leading-relaxed mb-3">
              Quando você opta pelo login com Google, utilizamos o protocolo
              OAuth 2.0 da Google LLC. Nesse processo, acessamos apenas as
              seguintes informações da sua conta Google:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Nome de exibição</li>
              <li>Endereço de e-mail</li>
              <li>Foto de perfil (opcional)</li>
            </ul>
            <p className="text-gray-600 leading-relaxed mt-3">
              Não solicitamos acesso a e-mails, contatos, calendários, arquivos
              do Drive nem qualquer outro dado além do listado acima. Você pode
              revogar esse acesso a qualquer momento em{" "}
              <a
                href="https://myaccount.google.com/permissions"
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                myaccount.google.com/permissions
              </a>
              .
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              5. Compartilhamento de dados
            </h2>
            <p className="text-gray-600 leading-relaxed">
              Seus dados <strong>não são vendidos</strong> nem compartilhados
              com terceiros para fins comerciais. Podemos compartilhá-los
              apenas nos seguintes casos:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600 mt-3">
              <li>
                Com prestadores de serviço que nos auxiliam na operação da
                plataforma (ex.: serviços de hospedagem e envio de e-mail),
                sob obrigação contratual de sigilo.
              </li>
              <li>
                Por exigência legal, como em resposta a ordem judicial.
              </li>
            </ul>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              6. Retenção e exclusão de dados
            </h2>
            <p className="text-gray-600 leading-relaxed">
              Seus dados são mantidos enquanto sua conta estiver ativa. Você
              pode solicitar a exclusão da sua conta e de todos os dados
              associados a qualquer momento enviando um e-mail para{" "}
              <a
                href="mailto:matheusbnas@gmail.com"
                className="text-blue-600 hover:underline"
              >
                matheusbnas@gmail.com
              </a>
              .
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              7. Segurança
            </h2>
            <p className="text-gray-600 leading-relaxed">
              Adotamos medidas técnicas e organizacionais para proteger seus
              dados contra acesso não autorizado, alteração, divulgação ou
              destruição, incluindo criptografia de senhas (bcrypt) e
              comunicação via HTTPS.
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              8. Seus direitos (LGPD)
            </h2>
            <p className="text-gray-600 leading-relaxed mb-3">
              Em conformidade com a Lei Geral de Proteção de Dados (Lei nº
              13.709/2018), você tem direito a:
            </p>
            <ul className="list-disc pl-6 space-y-2 text-gray-600">
              <li>Confirmar a existência de tratamento dos seus dados.</li>
              <li>Acessar os dados que temos sobre você.</li>
              <li>Corrigir dados incompletos, inexatos ou desatualizados.</li>
              <li>
                Solicitar anonimização, bloqueio ou eliminação de dados
                desnecessários.
              </li>
              <li>Revogar consentimento a qualquer momento.</li>
            </ul>
            <p className="text-gray-600 leading-relaxed mt-3">
              Para exercer qualquer desses direitos, entre em contato pelo
              e-mail{" "}
              <a
                href="mailto:matheusbnas@gmail.com"
                className="text-blue-600 hover:underline"
              >
                matheusbnas@gmail.com
              </a>
              .
            </p>
          </section>

          <section className="mb-8">
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              9. Cookies
            </h2>
            <p className="text-gray-600 leading-relaxed">
              Utilizamos apenas cookies essenciais para o funcionamento da
              sessão e autenticação. Não utilizamos cookies de rastreamento
              ou publicidade de terceiros.
            </p>
          </section>

          <section>
            <h2 className="text-xl font-semibold text-gray-800 mb-3">
              10. Contato
            </h2>
            <p className="text-gray-600 leading-relaxed">
              Dúvidas sobre esta política podem ser enviadas para:{" "}
              <a
                href="mailto:matheusbnas@gmail.com"
                className="text-blue-600 hover:underline"
              >
                matheusbnas@gmail.com
              </a>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default PrivacyPolicyPage;
