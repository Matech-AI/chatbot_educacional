#!/usr/bin/env python3
"""
Sistema de Guardrails para proteção de dados e conteúdo inadequado.
Implementa verificações de segurança para evitar vazamento de informações sensíveis.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ContentCategory(Enum):
    """Categorias de conteúdo para classificação."""
    SAFE = "safe"
    SENSITIVE = "sensitive"
    INAPPROPRIATE = "inappropriate"
    VIOLENCE = "violence"
    SEXUAL = "sexual"
    PERSONAL_DATA = "personal_data"
    MEDICAL = "medical"
    FINANCIAL = "financial"


@dataclass
class GuardrailResult:
    """Resultado da verificação de guardrails."""
    is_safe: bool
    category: ContentCategory
    confidence: float
    flagged_content: List[str]
    recommendations: List[str]
    risk_level: str  # "low", "medium", "high", "critical"


class ContentGuardrails:
    """Sistema de guardrails para proteção de conteúdo."""

    def __init__(self):
        # 🚨 PATRÕES CRÍTICOS DE SEGURANÇA

        # Dados pessoais e sensíveis
        self.personal_data_patterns = {
            "cpf": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
            "cnpj": r"\b\d{2}\.?\d{3}\.?\d{3}/?0001-\d{2}\b",
            "rg": r"\b\d{1,2}\.?\d{3}\.?\d{3}-?\d{1}\b",
            "telefone": r"\b\(?\d{2}\)?\s?\d{4,5}-?\d{4}\b",
            "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "endereco": r"\b(Rua|Avenida|Av\.|R\.|Alameda|Travessa)\s+[A-Za-zÀ-ÿ\s]+\s*,\s*\d+\s*-\s*[A-Za-zÀ-ÿ\s]+\b",
            "cep": r"\b\d{5}-?\d{3}\b",
            "data_nascimento": r"\b\d{1,2}/\d{1,2}/\d{4}\b",
            "cartao_credito": r"\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b",
            "senha": r"\b(senha|password|pwd)\s*[:=]\s*\S+\b",
            "usuario": r"\b(usuario|username|user|login)\s*[:=]\s*\S+\b"
        }

        # Conteúdo inadequado
        self.inappropriate_patterns = {
            "violencia": [
                r"\b(matar|assassinar|suicidio|homicidio|violencia|agressao|briga|guerra)\b",
                r"\b(arma|faca|pistola|bala|tiro|explosao|bomba)\b",
                r"\b(tortura|sequestro|estupro|abuso|agressao)\b"
            ],
            "sexual": [
                r"\b(erotico|pornografico|nudez|intimo|prostituicao|trafico|exploracao|pedofilia)\b",
                r"\b(orgasmo|erecao|penetracao|vagina|penis)\b"
            ],
            "drogas": [
                r"\b(maconha|cocaina|heroina|metanfetamina|ecstasy|trafico|contrabando|dependencia|overdose)\b",
                r"\b(alcool|tabaco|nicotina|fumar|beber)\b"
            ],
            "discriminacao": [
                r"\b(racismo|homofobia|xenofobia|antisemitismo|machismo)\b",
                r"\b(odio|preconceito|discriminacao|bullying|cyberbullying)\b"
            ]
        }

        # Palavras-chave de contexto educacional (permitidas)
        self.educational_whitelist = [
            "educacao", "fisica", "treinamento", "exercicio", "musculo",
            "forca", "hipertrofia", "condicionamento", "saude", "bem-estar",
            "anatomia", "fisiologia", "biomecanica", "nutricao", "recuperacao",
            "periodizacao", "planejamento", "avaliacao", "prescricao"
        ]

        # Configurações de sensibilidade
        self.sensitivity_thresholds = {
            "personal_data": 0.7,      # 70% de confiança para bloquear
            "inappropriate": 0.8,      # 80% de confiança para bloquear
            "violence": 0.9,           # 90% de confiança para bloquear
            "sexual": 0.9,             # 90% de confiança para bloquear
        }

        # Contextos permitidos para certos termos
        self.allowed_contexts = {
            "morte": ["celular", "bateria", "energia", "musculo", "celular", "fisiologia", "anatomia"],
            "violencia": ["domestica", "familiar", "social", "assistencia", "protecao"],
            "drogas": ["medicamento", "remedio", "prescricao", "medica", "medicina"],
            "sexo": ["genero", "caracteristica", "biologica", "educacao", "saude"]
        }

    def analyze_content(self, text: str, context: str = "") -> GuardrailResult:
        """
        Analisa o conteúdo para identificar riscos de segurança.

        Args:
            text: Texto a ser analisado
            context: Contexto adicional para análise

        Returns:
            GuardrailResult com resultado da análise
        """
        try:
            text_lower = text.lower()
            context_lower = context.lower()

            # 🔍 VERIFICAÇÕES DE SEGURANÇA

            # 1. Verificar dados pessoais
            personal_data_found = self._check_personal_data(text_lower)

            # 2. Verificar conteúdo inadequado
            inappropriate_content = self._check_inappropriate_content(
                text_lower, context_lower)

            # 3. Verificar contexto educacional
            educational_context = self._check_educational_context(
                text_lower, context_lower)

            # 4. Calcular risco geral
            risk_assessment = self._calculate_risk(
                personal_data_found,
                inappropriate_content,
                educational_context
            )

            # 5. Gerar recomendações
            recommendations = self._generate_recommendations(
                personal_data_found,
                inappropriate_content,
                risk_assessment
            )

            return GuardrailResult(
                is_safe=risk_assessment["is_safe"],
                category=risk_assessment["category"],
                confidence=risk_assessment["confidence"],
                flagged_content=risk_assessment["flagged_content"],
                recommendations=recommendations,
                risk_level=risk_assessment["risk_level"]
            )

        except Exception as e:
            logger.error(f"❌ Erro na análise de guardrails: {e}")
            # Em caso de erro, retornar resultado conservador (seguro)
            return GuardrailResult(
                is_safe=False,
                category=ContentCategory.SENSITIVE,
                confidence=1.0,
                flagged_content=["Erro na análise de segurança"],
                recommendations=["Revisar conteúdo manualmente"],
                risk_level="high"
            )

    def _check_personal_data(self, text: str) -> Dict[str, Any]:
        """Verifica se há dados pessoais no texto."""
        found_patterns = {}
        total_matches = 0

        for pattern_name, pattern in self.personal_data_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                found_patterns[pattern_name] = matches
                total_matches += len(matches)

        return {
            "found": bool(found_patterns),
            "patterns": found_patterns,
            "count": total_matches,
            "risk_level": "critical" if total_matches > 0 else "low"
        }

    def _check_inappropriate_content(self, text: str, context: str) -> Dict[str, Any]:
        """Verifica se há conteúdo inadequado."""
        found_content = {}
        total_risk_score = 0

        for category, patterns in self.inappropriate_patterns.items():
            category_matches = []
            category_score = 0

            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # Verificar se o contexto permite o termo
                    if self._is_context_allowed(matches, context, category):
                        continue

                    category_matches.extend(matches)
                    category_score += len(matches) * \
                        self._get_category_weight(category)

            if category_matches:
                found_content[category] = {
                    "matches": category_matches,
                    "score": category_score,
                    "risk_level": self._get_risk_level(category_score)
                }
                total_risk_score += category_score

        return {
            "found": bool(found_content),
            "categories": found_content,
            "total_score": total_risk_score,
            "risk_level": self._get_risk_level(total_risk_score)
        }

    def _check_educational_context(self, text: str, context: str) -> Dict[str, Any]:
        """Verifica se o contexto é educacional."""
        educational_terms = sum(
            1 for term in self.educational_whitelist if term in text)
        context_educational = any(
            term in context for term in self.educational_whitelist)

        return {
            "educational_terms": educational_terms,
            "context_educational": context_educational,
            "is_educational": educational_terms > 0 or context_educational
        }

    def _is_context_allowed(self, matches: List[str], context: str, category: str) -> bool:
        """Verifica se o contexto permite o uso de termos sensíveis."""
        if category in self.allowed_contexts:
            allowed_contexts = self.allowed_contexts[category]
            return any(allowed in context.lower() for allowed in allowed_contexts)
        return False

    def _get_category_weight(self, category: str) -> float:
        """Retorna o peso de risco para cada categoria."""
        weights = {
            "violencia": 3.0,
            "sexual": 3.0,
            "drogas": 2.5,
            "discriminacao": 2.0
        }
        return weights.get(category, 1.0)

    def _get_risk_level(self, score: float) -> str:
        """Converte score em nível de risco."""
        if score == 0:
            return "low"
        elif score < 3:
            return "medium"
        elif score < 6:
            return "high"
        else:
            return "critical"

    def _calculate_risk(self, personal_data: Dict, inappropriate: Dict, educational: Dict) -> Dict[str, Any]:
        """Calcula o risco geral do conteúdo."""
        risk_score = 0
        flagged_content = []
        category = ContentCategory.SAFE

        # Dados pessoais = risco crítico
        if personal_data["found"]:
            risk_score += 10
            flagged_content.extend(
                [f"Dados pessoais: {k}" for k in personal_data["patterns"].keys()])
            category = ContentCategory.PERSONAL_DATA

        # Conteúdo inadequado
        if inappropriate["found"]:
            risk_score += inappropriate["total_score"]
            for cat, data in inappropriate["categories"].items():
                flagged_content.extend(
                    [f"{cat}: {', '.join(data['matches'][:3])}"])

            if category == ContentCategory.SAFE:
                if "violence" in inappropriate["categories"]:
                    category = ContentCategory.VIOLENCE
                elif "sexual" in inappropriate["categories"]:
                    category = ContentCategory.SEXUAL
                else:
                    category = ContentCategory.INAPPROPRIATE

        # Contexto educacional pode reduzir o risco
        if educational["is_educational"] and risk_score < 5:
            risk_score = max(0, risk_score - 2)

        # Determinar se é seguro
        is_safe = risk_score < 3

        # Calcular confiança
        confidence = min(1.0, risk_score / 10.0)

        return {
            "is_safe": is_safe,
            "category": category,
            "confidence": confidence,
            "flagged_content": flagged_content,
            "risk_level": self._get_risk_level(risk_score)
        }

    def _generate_recommendations(self, personal_data: Dict, inappropriate: Dict, risk_assessment: Dict) -> List[str]:
        """Gera recomendações baseadas nos riscos encontrados."""
        recommendations = []

        if personal_data["found"]:
            recommendations.append(
                "🚨 REMOVER IMEDIATAMENTE todos os dados pessoais identificados")
            recommendations.append(
                "🔒 Substituir por placeholders genéricos (ex: [CPF], [NOME])")
            recommendations.append("📋 Revisar manualmente todo o conteúdo")

        if inappropriate["found"]:
            if inappropriate["total_score"] >= 6:
                recommendations.append(
                    "❌ BLOQUEAR conteúdo - risco crítico identificado")
            elif inappropriate["total_score"] >= 3:
                recommendations.append(
                    "⚠️ REVISAR conteúdo - risco alto identificado")
            else:
                recommendations.append(
                    "🔍 Verificar contexto dos termos sensíveis")

            recommendations.append(
                "📚 Confirmar se o contexto é educacionalmente apropriado")
            recommendations.append(
                "✂️ Remover ou reescrever seções problemáticas")

        if risk_assessment["risk_level"] in ["high", "critical"]:
            recommendations.append("🛡️ Implementar revisão manual obrigatória")
            recommendations.append("📋 Criar relatório de segurança detalhado")

        if not recommendations:
            recommendations.append(
                "✅ Conteúdo seguro - nenhuma ação necessária")

        return recommendations

    def sanitize_content(self, text: str, context: str = "") -> Tuple[str, GuardrailResult]:
        """
        Sanitiza o conteúdo removendo ou substituindo informações sensíveis.

        Args:
            text: Texto a ser sanitizado
            context: Contexto para análise

        Returns:
            Tuple com texto sanitizado e resultado da análise
        """
        # Primeiro analisar o conteúdo
        analysis = self.analyze_content(text, context)

        if analysis.is_safe:
            return text, analysis

        # Sanitizar dados pessoais
        sanitized_text = text
        for pattern_name, pattern in self.personal_data_patterns.items():
            if pattern_name in ["cpf", "cnpj", "rg"]:
                sanitized_text = re.sub(
                    pattern, f"[{pattern_name.upper()}]", sanitized_text)
            elif pattern_name in ["telefone", "email"]:
                sanitized_text = re.sub(
                    pattern, f"[{pattern_name.upper()}]", sanitized_text)
            elif pattern_name in ["endereco", "cep"]:
                sanitized_text = re.sub(
                    pattern, f"[{pattern_name.upper()}]", sanitized_text)
            elif pattern_name in ["data_nascimento"]:
                sanitized_text = re.sub(
                    pattern, "[DATA_NASCIMENTO]", sanitized_text)
            elif pattern_name in ["cartao_credito"]:
                sanitized_text = re.sub(
                    pattern, "[CARTAO_CREDITO]", sanitized_text)
            elif pattern_name in ["senha", "usuario"]:
                sanitized_text = re.sub(
                    pattern, f"[{pattern_name.upper()}]", sanitized_text)

        # Adicionar aviso de segurança
        if not analysis.is_safe:
            security_warning = f"""

🚨 **AVISO DE SEGURANÇA - CONTEÚDO SANITIZADO**

⚠️ **RISCOS IDENTIFICADOS:**
{chr(10).join(f"- {content}" for content in analysis.flagged_content[:3])}

🛡️ **AÇÕES TOMADAS:**
- Dados pessoais foram substituídos por placeholders
- Conteúdo sensível foi marcado para revisão
- Recomenda-se verificação manual

📋 **RECOMENDAÇÕES:**
{chr(10).join(f"- {rec}" for rec in analysis.recommendations[:3])}

🔒 **Nível de Risco:** {analysis.risk_level.upper()}
"""
            sanitized_text += security_warning

        return sanitized_text, analysis

    def validate_response(self, response: str, original_question: str = "") -> GuardrailResult:
        """
        Valida uma resposta gerada pelo sistema.

        Args:
            response: Resposta a ser validada
            original_question: Pergunta original para contexto

        Returns:
            GuardrailResult com resultado da validação
        """
        return self.analyze_content(response, original_question)

    def get_security_report(self, content: str, context: str = "") -> Dict[str, Any]:
        """
        Gera um relatório detalhado de segurança.

        Args:
            content: Conteúdo analisado
            context: Contexto adicional

        Returns:
            Relatório de segurança detalhado
        """
        analysis = self.analyze_content(content, context)

        return {
            "timestamp": "2024-01-01T00:00:00Z",  # Implementar datetime real
            "content_length": len(content),
            "security_analysis": {
                "overall_risk": analysis.risk_level,
                "is_safe": analysis.is_safe,
                "confidence": analysis.confidence,
                "category": analysis.category.value
            },
            "flagged_issues": analysis.flagged_content,
            "recommendations": analysis.recommendations,
            "risk_breakdown": {
                "personal_data": bool(analysis.category == ContentCategory.PERSONAL_DATA),
                "inappropriate_content": analysis.category in [ContentCategory.VIOLENCE, ContentCategory.SEXUAL, ContentCategory.INAPPROPRIATE],
                "sensitive_information": analysis.category == ContentCategory.SENSITIVE
            },
            "compliance": {
                "gdpr_compliant": analysis.is_safe and analysis.category != ContentCategory.PERSONAL_DATA,
                "educational_appropriate": analysis.is_safe or analysis.risk_level in ["low", "medium"],
                "requires_review": not analysis.is_safe
            }
        }


# Instância global para uso em outros módulos
content_guardrails = ContentGuardrails()


def validate_and_sanitize_content(text: str, context: str = "") -> Tuple[str, GuardrailResult]:
    """
    Função de conveniência para validar e sanitizar conteúdo.

    Args:
        text: Texto a ser processado
        context: Contexto adicional

    Returns:
        Tuple com texto processado e resultado da análise
    """
    return content_guardrails.sanitize_content(text, context)


def is_content_safe(text: str, context: str = "") -> bool:
    """
    Verifica rapidamente se o conteúdo é seguro.

    Args:
        text: Texto a ser verificado
        context: Contexto adicional

    Returns:
        True se o conteúdo for seguro, False caso contrário
    """
    result = content_guardrails.analyze_content(text, context)
    return result.is_safe


if __name__ == "__main__":
    # Teste do sistema de guardrails
    test_texts = [
        "Meu CPF é 123.456.789-00 e moro na Rua das Flores, 123",
        "Vamos falar sobre hipertrofia muscular e treinamento de força",
        "Este é um conteúdo sobre violência doméstica e como ajudar",
        "Minha senha é 123456 e meu email é teste@email.com"
    ]

    guardrails = ContentGuardrails()

    for i, text in enumerate(test_texts, 1):
        print(f"\n{'='*50}")
        print(f"TESTE {i}: {text[:50]}...")

        result = guardrails.analyze_content(text)
        print(f"Seguro: {result.is_safe}")
        print(f"Categoria: {result.category.value}")
        print(f"Risco: {result.risk_level}")
        print(f"Conteúdo marcado: {result.flagged_content}")
        print(f"Recomendações: {result.recommendations}")

        if not result.is_safe:
            sanitized, _ = guardrails.sanitize_content(text)
            print(f"Texto sanitizado: {sanitized[:100]}...")
