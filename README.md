# erp-comecyt-api

Proyecto de hackathon: API para un ERP y un microservicio público para una app móvil.

Descripción
-----------
ERP-COMECYT-API es una solución creada en el marco de un hackathon que provee:
- Una API interna para la gestión de recursos (usuarios, roles, productos, inventario, ventas).
- Un microservicio público y ligero pensado para ser consumido por una aplicación móvil (autenticación, catálogo público, notificaciones).

Arquitectura
------------
- API principal (backend): servicio RESTful que expone las operaciones del ERP.
- Microservicio público: puertas de enlace (gateway) con endpoints seguros y limitados para la app móvil.
- Persistencia: base de datos relacional (p. ej. PostgreSQL).
- Despliegue: contenedores Docker y/o hosting en la nube.
- Comunicación interna por HTTP/JSON; autenticación JWT para clientes móviles.



