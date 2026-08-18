# firmware-release-skill Eval Spec

回归门禁：固件类型识别、命名解析与端到端发布路由。运行方式：

```bash
python3 scripts/run_evals.py          # 在技能根目录运行
python3 scripts/run_evals.py --json
```

```json
{
  "skill": "firmware-release-skill",
  "criteria": [
    {
      "id": "classify-bcmu",
      "text": "BCMU 命名固件识别为 bcmu",
      "criterion": "BCMU 命名固件识别为 bcmu",
      "type": "command",
      "cmd": "python -c \"import sys; sys.path.insert(0,'scripts'); from release import classify_firmware; assert classify_firmware('BCMU_V5.1.7.12_\\u7ec420_20260818_\\u6821\\u9a8c0x0CCB38FA.bin') == 'bcmu'\""
    },
    {
      "id": "classify-hmi",
      "text": "AppManager exe 安装包识别为 hmi",
      "criterion": "AppManager exe 安装包识别为 hmi",
      "type": "command",
      "cmd": "python -c \"import sys; sys.path.insert(0,'scripts'); from release import classify_firmware; assert classify_firmware('AppManagerSetup_1.0.3.21_release.exe') == 'hmi'\""
    },
    {
      "id": "classify-bmu",
      "text": "BMU 命名固件识别为 bmu（与 BCMU 区分）",
      "criterion": "BMU 命名固件识别为 bmu（注意与 BCMU 区分）",
      "type": "command",
      "cmd": "python -c \"import sys; sys.path.insert(0,'scripts'); from release import classify_firmware; assert classify_firmware('BMU_V1.0.0_\\u7ec41_20260818_\\u6821\\u9a8c0x1A2B3C4D.bin') == 'bmu'\""
    },
    {
      "id": "classify-unknown",
      "text": "无产品标识的文件返回 None 而非猜测",
      "criterion": "无产品标识的文件返回 None 而非猜测",
      "type": "command",
      "cmd": "python -c \"import sys; sys.path.insert(0,'scripts'); from release import classify_firmware; assert classify_firmware('random_notes.txt') is None\""
    },
    {
      "id": "parse-name",
      "text": "发布命名解析出 product/ver/group/date/crc 五字段",
      "criterion": "发布命名解析出 product/ver/group/date/crc 五字段",
      "type": "command",
      "cmd": "python -c \"import sys; sys.path.insert(0,'scripts'); from release import parse_release_name; i = parse_release_name('BCMU_V5.1.7.12_\\u7ec420_20260818_\\u6821\\u9a8c0x0CCB38FA.bin'); assert i['product']=='BCMU' and i['ver']=='5.1.7.12' and i['group']=='20' and i['date']=='20260818' and i['crc']=='0x0CCB38FA'\""
    },
    {
      "id": "e2e-route",
      "text": "端到端：发现发布对→自动分类→复制到正确子目录",
      "criterion": "端到端：发现发布对→自动分类→复制到正确子目录",
      "type": "command",
      "cmd": "python -c \"import sys,tempfile,pathlib; sys.path.insert(0,'scripts'); import release; d=tempfile.mkdtemp(); p=pathlib.Path(d); (p/'BCMU_V5.1.7.12_\\u7ec499_20260818_\\u6821\\u9a8c0x11223344.bin').write_bytes(b'\\x00'*16); (p/'BCMU_V5.1.7.12_\\u7ec499_20260818_\\u6821\\u9a8c0x11223344.hex').write_text('x'); pairs=release.find_published_pairs(d); assert len(pairs)==1; cat,_=release._categorize([pairs[0]['bin']],None); assert cat=='bcmu'; release.publish_files([pairs[0]['bin']], release.resolve_release_dir(p/'repo','bcmu')); assert (p/'repo'/'bcmu'/'BCMU_V5.1.7.12_\\u7ec499_20260818_\\u6821\\u9a8c0x11223344.bin').exists()\""
    }
  ],
  "golden": [
    {
      "id": "bcmu-sample",
      "input": "golden/bcmu-sample/input.txt",
      "expected": null,
      "expected_status": "pending-first-green",
      "split": "val"
    },
    {
      "id": "hmi-sample",
      "input": "golden/hmi-sample/input.txt",
      "expected": null,
      "expected_status": "pending-first-green",
      "split": "val"
    },
    {
      "id": "unknown-sample",
      "input": "golden/unknown-sample/input.txt",
      "expected": null,
      "expected_status": "pending-first-green",
      "split": "test"
    }
  ]
}
```
