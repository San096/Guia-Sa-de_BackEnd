ORIENTACOES = [
    # ----------- ALERTA GRAVE -----------
    {
        "id": "emergencia",
        "sintomas": [
            "falta_ar",
            "dor_peito",
            "desmaio_confusao",
        ],
        "mensagem": "Procure imediatamente uma UPA ou hospital.",
        "tiposPermitidos": ["upa", "hospital"],
        "prioridade": 10,
    },

    # ----------- SAÚDE MENTAL / CAPS -----------
    {
        "id": "caps",
        "sintomas": [
            "ansiedade_intensa",
            "depressao",
            "insônia_grave",
            "ideacao_suicida",
            "surto_psicotico",
        ],
        "mensagem": "Procure um CAPS para atendimento especializado em saúde mental.",
        "tiposPermitidos": ["caps"],
        "prioridade": 8,
    },

    # ----------- CASOS GERAIS -----------
    {
        "id": "geral",
        "sintomas": [
            "febre",
            "tosse",
            "dor_garganta",
            "dor_cabeca",
            "vomitos",
            "diarreia",
            "dor_abdominal_intensa",
        ],
        "mensagem": "Procure uma Unidade Básica de Saúde (UBS).",
        "tiposPermitidos": ["ubs"],
        "prioridade": 3,
    },
]
