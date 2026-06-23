-- create database stock_db;

use stock_db;

-- stock_db.kor_fs definition

CREATE TABLE `kor_fs` (
  `계정` varchar(30) NOT NULL,
  `기준일` date NOT NULL,
  `값` float DEFAULT NULL,
  `종목코드` varchar(6) NOT NULL,
  `공시구분` varchar(1) NOT NULL,
  PRIMARY KEY (`계정`,`기준일`,`종목코드`,`공시구분`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_fs_per definition

CREATE TABLE `kor_fs_per` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `주가` double DEFAULT NULL,
  `외국인보유비중` double DEFAULT NULL,
  `상대수익률` double DEFAULT NULL,
  `PER` text,
  `PER_12M` double DEFAULT NULL,
  `업종PER` double DEFAULT NULL,
  `PBR` text,
  `DY` text,
  `거래량` double DEFAULT NULL,
  `거래대금` double DEFAULT NULL,
  `시가총액` double DEFAULT NULL,
  `시가총액_보통주` double DEFAULT NULL,
  `per_pbr` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_fs_value definition

CREATE TABLE `kor_fs_value` (
  `종목코드` varchar(6) NOT NULL,
  `종목명` varchar(20) DEFAULT NULL,
  `기준일` date NOT NULL,
  `주가` float DEFAULT NULL,
  `외국인보유비중` float DEFAULT NULL,
  `상대수익률` float DEFAULT NULL,
  `PER` float DEFAULT NULL,
  `PER_12M` float DEFAULT NULL,
  `업종PER` float DEFAULT NULL,
  `PBR` float DEFAULT NULL,
  `DY` float DEFAULT NULL,
  `거래량` float DEFAULT NULL,
  `거래대금` float DEFAULT NULL,
  `시가총액` float DEFAULT NULL,
  `시가총액_보통주` float DEFAULT NULL,
  PRIMARY KEY (`종목코드`,`기준일`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_magic_rank definition

CREATE TABLE `kor_magic_rank` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `시가총액` double DEFAULT NULL,
  `감가상각비` text,
  `당기순이익` double DEFAULT NULL,
  `매출액` text,
  `법인세비용` text,
  `부채` double DEFAULT NULL,
  `비유동자산` text,
  `유동부채` text,
  `유동자산` text,
  `이자비용` text,
  `현금및현금성자산` text,
  `이익 수익률` text,
  `투하자본 수익률` text,
  `투자구분` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_magic_rank4 definition

CREATE TABLE `kor_magic_rank4` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `시가총액` double DEFAULT NULL,
  `감가상각비` text,
  `당기순이익` text,
  `매출액` text,
  `법인세비용` text,
  `부채` text,
  `비유동자산` text,
  `유동부채` text,
  `유동자산` text,
  `이자비용` text,
  `현금및현금성자산` text,
  `이익 수익률` text,
  `투하자본 수익률` text,
  `투자구분` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_multi_factor definition

CREATE TABLE `kor_multi_factor` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `SEC_NM_KOR` text,
  `자본` double DEFAULT NULL,
  `자산` double DEFAULT NULL,
  `당기순이익` double DEFAULT NULL,
  `매출총이익` double DEFAULT NULL,
  `영업활동으로인한현금흐름` double DEFAULT NULL,
  `ROE` double DEFAULT NULL,
  `GPA` double DEFAULT NULL,
  `CFO` double DEFAULT NULL,
  `DY` double DEFAULT NULL,
  `PBR` double DEFAULT NULL,
  `PCR` double DEFAULT NULL,
  `PER` double DEFAULT NULL,
  `PSR` double DEFAULT NULL,
  `12M` double DEFAULT NULL,
  `K_ratio` double DEFAULT NULL,
  `z_quality` double DEFAULT NULL,
  `z_value` double DEFAULT NULL,
  `z_momentum` double DEFAULT NULL,
  `qvm` double DEFAULT NULL,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_multi_factor4 definition

CREATE TABLE `kor_multi_factor4` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `SEC_NM_KOR` text,
  `자본` text,
  `자산` text,
  `당기순이익` text,
  `매출총이익` text,
  `영업활동으로인한현금흐름` text,
  `ROE` text,
  `GPA` text,
  `CFO` text,
  `DY` text,
  `PBR` text,
  `PCR` text,
  `PER` text,
  `PSR` text,
  `12M` text,
  `K_ratio` text,
  `z_quality` text,
  `z_value` text,
  `z_momentum` text,
  `qvm` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_per_dy definition

CREATE TABLE `kor_per_dy` (
  `종목코드` text,
  `종목명` text,
  `시장구분` text,
  `종가` double DEFAULT NULL,
  `시가총액` double DEFAULT NULL,
  `기준일` date DEFAULT NULL,
  `EPS` text,
  `BPS` text,
  `PER` text,
  `PBR` text,
  `주당배당금` double DEFAULT NULL,
  `배당수익률` text,
  `종목구분` text,
  `per_pbr` text,
  `dy` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_per_pbr definition

CREATE TABLE `kor_per_pbr` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `DY` text,
  `PBR` text,
  `PCR` text,
  `PER` text,
  `PSR` text,
  `per_pbr` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_per_pbr4 definition

CREATE TABLE `kor_per_pbr4` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `DY` text,
  `PBR` text,
  `PCR` text,
  `PER` text,
  `PSR` text,
  `per_pbr` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_price definition

CREATE TABLE `kor_price` (
  `날짜` date NOT NULL,
  `시가` double DEFAULT NULL,
  `고가` double DEFAULT NULL,
  `저가` double DEFAULT NULL,
  `종가` double DEFAULT NULL,
  `거래량` double DEFAULT NULL,
  `외국인소진율` double DEFAULT NULL,
  `종목코드` varchar(6) NOT NULL,
  PRIMARY KEY (`날짜`,`종목코드`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_quality definition

CREATE TABLE `kor_quality` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `당기순이익` double DEFAULT NULL,
  `매출총이익` double DEFAULT NULL,
  `영업활동으로인한현금흐름` double DEFAULT NULL,
  `자본` double DEFAULT NULL,
  `자산` double DEFAULT NULL,
  `ROE` double DEFAULT NULL,
  `GPA` double DEFAULT NULL,
  `CFO` double DEFAULT NULL,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_quality4 definition

CREATE TABLE `kor_quality4` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `당기순이익` text,
  `매출총이익` text,
  `영업활동으로인한현금흐름` text,
  `자본` text,
  `자산` text,
  `ROE` text,
  `GPA` text,
  `CFO` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_ratio_12 definition

CREATE TABLE `kor_ratio_12` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `momentum` text,
  `K_ratio` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_ratio_3 definition

CREATE TABLE `kor_ratio_3` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `momentum` text,
  `K_ratio` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_ratio_6 definition

CREATE TABLE `kor_ratio_6` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `momentum` text,
  `K_ratio` text,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_sector definition

CREATE TABLE `kor_sector` (
  `IDX_CD` varchar(3) DEFAULT NULL,
  `CMP_CD` varchar(6) NOT NULL,
  `CMP_KOR` varchar(20) DEFAULT NULL,
  `SEC_NM_KOR` varchar(10) DEFAULT NULL,
  `기준일` date NOT NULL,
  PRIMARY KEY (`CMP_CD`,`기준일`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_ticker definition

CREATE TABLE `kor_ticker` (
  `종목코드` varchar(6) NOT NULL,
  `종목명` varchar(20) DEFAULT NULL,
  `시장구분` varchar(6) DEFAULT NULL,
  `종가` float DEFAULT NULL,
  `시가총액` float DEFAULT NULL,
  `기준일` date NOT NULL,
  `EPS` float DEFAULT NULL,
  `BPS` float DEFAULT NULL,
  `PER` float DEFAULT NULL,
  `PBR` float DEFAULT NULL,
  `주당배당금` float DEFAULT NULL,
  `배당수익률` float DEFAULT NULL,
  `종목구분` varchar(5) DEFAULT NULL,
  PRIMARY KEY (`종목코드`,`기준일`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_value definition

CREATE TABLE `kor_value` (
  `종목코드` varchar(6) NOT NULL,
  `기준일` date NOT NULL,
  `지표` varchar(3) NOT NULL,
  `값` double DEFAULT NULL,
  PRIMARY KEY (`종목코드`,`기준일`,`지표`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.kor_value4 definition

CREATE TABLE `kor_value4` (
  `종목코드` varchar(6) NOT NULL,
  `기준일` date NOT NULL,
  `지표` varchar(3) NOT NULL,
  `값` double DEFAULT NULL,
  PRIMARY KEY (`종목코드`,`기준일`,`지표`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.sample_etf definition

CREATE TABLE `sample_etf` (
  `Date` datetime DEFAULT NULL,
  `SPY` double DEFAULT NULL,
  `IEV` double DEFAULT NULL,
  `EWJ` double DEFAULT NULL,
  `EEM` double DEFAULT NULL,
  `TLT` double DEFAULT NULL,
  `IEF` double DEFAULT NULL,
  `IYR` double DEFAULT NULL,
  `RWX` double DEFAULT NULL,
  `GLD` double DEFAULT NULL,
  `DBC` double DEFAULT NULL,
  KEY `ix_sample_etf_Date` (`Date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.target definition

CREATE TABLE `target` (
  `종목코드` text,
  `현재가` bigint DEFAULT NULL,
  `보유수량` bigint DEFAULT NULL,
  `목표수량` double DEFAULT NULL,
  `투자수량` double DEFAULT NULL,
  `CMP_KOR` text,
  `SEC_NM_KOR` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- stock_db.`결과_260506` definition

CREATE TABLE `결과_260506` (
  `종목코드` mediumtext,
  `종목명` mediumtext,
  `시장구분` varchar(6) DEFAULT NULL,
  `종가` float DEFAULT NULL,
  `거래량` double DEFAULT NULL,
  `시총` double DEFAULT NULL,
  `순위` bigint unsigned NOT NULL DEFAULT '0',
  `gubun` varchar(13) NOT NULL DEFAULT ''
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- stock_db.global_fs definition

CREATE TABLE `global_fs` (
  `계정` text,
  `기준일` date DEFAULT NULL,
  `값` double DEFAULT NULL,
  `종목코드` text,
  `공시구분` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.global_multi_factor definition

CREATE TABLE `global_multi_factor` (
  `종목코드` text,
  `종목명` text,
  `기준일` date DEFAULT NULL,
  `SEC_NM_KOR` text,
  `자본` double DEFAULT NULL,
  `자산` double DEFAULT NULL,
  `당기순이익` double DEFAULT NULL,
  `매출총이익` double DEFAULT NULL,
  `영업활동으로인한현금흐름` double DEFAULT NULL,
  `ROE` double DEFAULT NULL,
  `GPA` double DEFAULT NULL,
  `CFO` double DEFAULT NULL,
  `DY` double DEFAULT NULL,
  `PBR` double DEFAULT NULL,
  `PCR` double DEFAULT NULL,
  `PER` double DEFAULT NULL,
  `PSR` double DEFAULT NULL,
  `12M` double DEFAULT NULL,
  `K_ratio` double DEFAULT NULL,
  `z_quality` double DEFAULT NULL,
  `z_value` double DEFAULT NULL,
  `z_momentum` double DEFAULT NULL,
  `qvm` double DEFAULT NULL,
  `invest` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.global_price definition

CREATE TABLE `global_price` (
  `날짜` date DEFAULT NULL,
  `시가` double DEFAULT NULL,
  `고가` double DEFAULT NULL,
  `저가` double DEFAULT NULL,
  `종가` double DEFAULT NULL,
  `거래량` bigint DEFAULT NULL,
  `종목코드` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.global_sector definition

CREATE TABLE `global_sector` (
  `IDX_CD` text,
  `CMP_CD` text,
  `CMP_KOR` text,
  `SEC_NM_KOR` text,
  `기준일` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.global_ticker definition

CREATE TABLE `global_ticker` (
  `종목코드` text,
  `종목명` text,
  `시장구분` text,
  `종가` bigint DEFAULT NULL,
  `시가총액` bigint DEFAULT NULL,
  `기준일` date DEFAULT NULL,
  `EPS` double DEFAULT NULL,
  `BPS` double DEFAULT NULL,
  `주당배당금` double DEFAULT NULL,
  `종목구분` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


-- stock_db.global_value definition

CREATE TABLE `global_value` (
  `종목코드` text,
  `기준일` date DEFAULT NULL,
  `지표` text,
  `값` double DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;