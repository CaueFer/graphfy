async def graph_generator(colunas: list[str]):
    try:
        print(colunas)
        return {"success": True, "graphValues": colunas}


    except Exception as e:
        return {"error": f"Erro ao gerar gráfico: {str(e)}"}
